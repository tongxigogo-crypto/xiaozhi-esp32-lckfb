#!/usr/bin/env python3
"""Prepare private NVS configuration offline. Never opens a device or prints values."""
import argparse
import base64
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from vendor.esp_idf_v6_1.nvs_parser import NVS_Partition

ENCODINGS = {"uint8_t":"u8", "int8_t":"i8", "uint16_t":"u16", "int16_t":"i16",
             "uint32_t":"u32", "int32_t":"i32", "uint64_t":"u64", "int64_t":"i64"}
ALLOWED = {("websocket","token"),("websocket","url"),("wifi","ota_url")}

def _require(condition):
    if not condition:
        raise ValueError("Invalid or ambiguous NVS/configuration; refusing to guess")

def _key(name):
    _require(isinstance(name,str) and 1 <= len(name) <= 15
             and all(32 <= ord(c) <= 126 for c in name))
    return name

def _payload(entry):
    data=b"".join(bytes(child.raw) for child in entry.children)
    size=entry.data["size"]
    _require(len(data)>=size)
    return data[:size]

def snapshot(raw):
    """Return namespace -> key -> (logical encoding, exact value). Fail closed."""
    _require(isinstance(raw,(bytes,bytearray)) and len(raw)>=12288 and len(raw)%4096==0)
    part=NVS_Partition("private-input",bytearray(raw))
    namespaces={}; entries=[]
    for page in part.pages:
        offset=page.start_address
        if page.is_empty:
            _require(bytes(raw[offset:offset+4096])==b"\xff"*4096)
            continue
        _require(page.header["status"] in {"Active","Full"} and page.header["version"]==2)
        _require(page.header["crc"]["original"]==page.header["crc"]["computed"])
        accounted=set()
        for entry in page.entries:
            _require(entry.state in {"Empty","Erased","Written"})
            if entry.state!="Written":
                continue
            meta=entry.metadata
            span=meta["span"]
            _require(1<=span<=126 and entry.index+span<=126 and len(entry.children)==span-1)
            _require(all(child.state=="Written" for child in entry.children))
            accounted.update(range(entry.index,entry.index+span))
            _require(meta["crc"]["original"]==meta["crc"]["computed"])
            kind=meta["type"]
            _require(kind in set(ENCODINGS)|{"string","blob","blob_data","blob_index"})
            if kind in {"string","blob","blob_data"}:
                _require(meta["crc"]["data_original"]==meta["crc"]["data_computed"])
                _require(len(entry.children)>0)
            else:
                _require(span==1)
            key=_key(entry.key)
            if meta["namespace"]==0:
                _require(kind=="uint8_t")
                idx=entry.data["value"]
                _require(0<idx<255 and idx not in namespaces and key not in namespaces.values())
                namespaces[idx]=key
            else:
                entries.append(entry)
        for i in range(126):
            state=(page.raw_entry_state_bitmap[i//4]>>((i%4)*2))&3
            _require(state in {0,2,3})
            if state==2:
                _require(i in accounted)
    result={name:{} for name in namespaces.values()}
    grouped={}
    for entry in entries:
        idx=entry.metadata["namespace"]
        _require(idx in namespaces)
        grouped.setdefault((idx,entry.key),[]).append(entry)
    for (idx,key),items in grouped.items():
        kinds={e.metadata["type"] for e in items}
        if kinds<= {"blob_data","blob_index"}:
            indices=[e for e in items if e.metadata["type"]=="blob_index"]
            _require(len(indices)==1)
            index=indices[0].data
            count,start=index["chunk_count"],index["chunk_start"]
            _require(count>0 and start+count<=256)
            chunks={}
            for entry in items:
                if entry.metadata["type"]=="blob_index":
                    continue
                chunk=entry.metadata["chunk_index"]
                _require(chunk not in chunks)
                chunks[chunk]=_payload(entry)
            _require(set(chunks)==set(range(start,start+count)))
            value=b"".join(chunks[i] for i in range(start,start+count))
            _require(len(value)==index["size"])
            logical=("blob",value)
        else:
            _require(len(items)==1)
            entry=items[0];kind=entry.metadata["type"]
            if kind in ENCODINGS:
                logical=(ENCODINGS[kind],entry.data["value"])
            elif kind=="string":
                value=_payload(entry)
                _require(value.endswith(b"\0") and b"\0" not in value[:-1])
                decoded=value[:-1].decode("utf-8")
                _require(decoded.encode("utf-8")+b"\0"==value)
                logical=("string",decoded)
            elif kind=="blob":
                logical=("blob",_payload(entry))
            else:
                raise ValueError("Unsupported NVS entry")
        result[namespaces[idx]][key]=logical
    return result

def generate(values,size):
    """Use the official low-level writer, bypassing CSV's Wi-Fi auto-injection."""
    from esp_idf_nvs_partition_gen import nvs_partition_gen as gen
    _require(size>=12288 and size%4096==0)
    out=io.BytesIO()
    with gen.nvs_open(out,size-4096,gen.Page.VERSION2) as nvs:
        for namespace,items in values.items():
            nvs.write_namespace(_key(namespace))
            for key,(encoding,value) in items.items():
                if encoding=="blob":
                    value=base64.b64encode(value).decode("ascii")
                    encoding="base64"
                nvs.write_entry(_key(key),value,encoding)
    raw=out.getvalue()
    _require(len(raw)==size and snapshot(raw)==values)
    return raw

def _credentials(credentials):
    _require(isinstance(credentials,dict) and set(credentials)=={"token","websocket_url","ota_url"})
    token=credentials["token"]
    _require(isinstance(token,str) and 32<=len(token)<=256
             and all(33<=ord(c)<=126 for c in token))
    ws=credentials["websocket_url"];ota=credentials["ota_url"]
    urls=[]
    for value,scheme in [(ws,"wss"),(ota,"https")]:
        _require(isinstance(value,str) and all(33<=ord(c)<=126 for c in value))
        parsed=urlsplit(value)
        _require(parsed.scheme==scheme and parsed.hostname and not parsed.username
                 and not parsed.password and not parsed.fragment and not parsed.query)
        _require(parsed.path.startswith("/") and parsed.port!=0)
        urls.append(parsed)
    _require(urls[0].hostname==urls[1].hostname)
    return token,ws,ota

def provision(raw,credentials,expected_mac):
    token,ws,ota=_credentials(credentials)
    original=snapshot(raw)
    _require(isinstance(expected_mac,str) and
             re.fullmatch(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}",expected_mac))
    _require(original.get("phy",{}).get("cal_mac")==("blob",bytes.fromhex(expected_mac.replace(":",""))))
    _require("websocket" in original and "wifi" in original)
    target=copy.deepcopy(original)
    target["websocket"]["token"]=("string",token)
    target["websocket"]["url"]=("string",ws)
    target["wifi"]["ota_url"]=("string",ota)
    result=generate(target,len(raw))
    actual=snapshot(result)
    _require(set(actual)==set(original))
    for ns,items in original.items():
        _require({k:v for k,v in actual[ns].items() if (ns,k) not in ALLOWED}
                 =={k:v for k,v in items.items() if (ns,k) not in ALLOWED})
    _require(actual==target)
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",required=True,type=Path)
    parser.add_argument("--credentials",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--expected-mac",required=True)
    args=parser.parse_args(argv)
    try:
        _require(args.credentials.stat().st_mode&0o077==0)
        original=args.input.read_bytes()
        credentials=json.loads(args.credentials.read_text(encoding="utf-8"))
        # The generator can print input values on exceptional paths; never forward it.
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result=provision(original,credentials,args.expected_mac)
        fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            with os.fdopen(fd,"wb") as output:
                output.write(result)
                output.flush()
                os.fsync(output.fileno())
        except BaseException:
            # Keep partial output private for diagnosis; never overwrite another file.
            raise
        print(json.dumps({"bytes":len(result),"sha256":hashlib.sha256(result).hexdigest(),
                          "namespaces":len(snapshot(result)),
                          "keys":sum(len(v) for v in snapshot(result).values()),
                          "allowed_target_keys":["websocket.token","websocket.url","wifi.ota_url"],
                          "other_logical_values_preserved":True}))
        return 0
    except Exception as error:
        print("Provisioning failed ("+type(error).__name__+"); no values logged.",file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
