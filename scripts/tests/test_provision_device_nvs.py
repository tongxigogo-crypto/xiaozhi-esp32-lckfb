"""Offline NVS preservation tests using public fixture values only."""
import base64
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from provision_device_nvs import snapshot, generate, provision

HAS_GENERATOR = importlib.util.find_spec("esp_idf_nvs_partition_gen") is not None
TOKEN = "public-fixture-token-never-use-in-production-0123456789"
MAC = bytes.fromhex("9c139e8ac774")

@unittest.skipUnless(HAS_GENERATOR, "run with esp-idf-nvs-partition-gen==0.3.0")
class ProvisionTests(unittest.TestCase):
    def fixture(self):
        return {
            "board": {"uuid": ("string", "fixture-device-uuid")},
            "empty": {},
            "wifi": {"ssid": ("string", "fixture-home"), "password": ("string", "fixture-pass"),
                     "ssid1": ("string", "fixture-hotspot"), "password1": ("string", "fixture-pass2")},
            "phy": {"cal_mac": ("blob", MAC), "large": ("blob", bytes(range(256)) * 25)},
            "websocket": {"url": ("string", "ws://example.test:8000/xiaozhi/v1/")},
            "numbers": {kind: (kind, value) for kind, value in
                        [("u8",255),("i8",-128),("u16",65535),("i16",-32768),
                         ("u32",4294967295),("i32",-2147483648),
                         ("u64",18446744073709551615),("i64",-9223372036854775808)]},
        }

    def creds(self):
        return {"token": TOKEN, "websocket_url": "wss://example.test/xiaozhi/v1/",
                "ota_url": "https://example.test/xiaozhi/ota/"}

    def test_all_types_chunks_empty_namespace_roundtrip(self):
        original = self.fixture()
        binary = generate(original, 16384)
        self.assertEqual(len(binary),16384)
        self.assertEqual(snapshot(binary), original)
        self.assertEqual(snapshot(generate(snapshot(binary),16384)), original)

    def test_only_approved_keys_change_and_generator_injects_nothing(self):
        original = self.fixture(); old = generate(original,16384)
        out = provision(old,self.creds(),"9c:13:9e:8a:c7:74")
        expected = copy.deepcopy(original)
        expected["websocket"]["token"] = ("string",TOKEN)
        expected["websocket"]["url"] = ("string",self.creds()["websocket_url"])
        expected["wifi"]["ota_url"] = ("string",self.creds()["ota_url"])
        self.assertEqual(snapshot(out),expected)

    def test_corrupt_page_entry_and_data_crc_rejected(self):
        original = generate(self.fixture(),16384)
        from vendor.esp_idf_v6_1.nvs_parser import NVS_Partition
        part=NVS_Partition("fixture",bytearray(original))
        entry=next(e for page in part.pages for e in page.entries
                   if e.state=="Written" and e.metadata["type"]=="string")
        parent=next(page for page in part.pages if entry in page.entries)
        for offset in [4,parent.start_address+64+entry.index*32+8,
                       parent.start_address+64+(entry.index+1)*32]:
            bad=bytearray(original);bad[offset]^=1
            with self.assertRaises(ValueError):snapshot(bytes(bad))
        with self.assertRaises(ValueError):snapshot(original[:-1])

    def test_duplicate_and_ambiguous_entries_rejected(self):
        from esp_idf_nvs_partition_gen import nvs_partition_gen as gen
        out=io.BytesIO()
        with gen.nvs_open(out,12288,gen.Page.VERSION2) as n:
            n.write_namespace("fixture")
            n.write_entry("same",1,"u8")
            n.write_entry("same",2,"u8")
        with self.assertRaises(ValueError):snapshot(out.getvalue())
        out=io.BytesIO()
        with gen.nvs_open(out,12288,gen.Page.VERSION2) as n:
            n.write_namespace("fixture")
            n.write_entry("blob",base64.b64encode(b"a"*4000).decode(),"base64")
            n.write_entry("blob",base64.b64encode(b"b"*4000).decode(),"base64")
        with self.assertRaises(ValueError):snapshot(out.getvalue())

    def test_bad_credentials_or_mac_rejected(self):
        raw=generate(self.fixture(),16384)
        for field,value in [("token","short"),("token",TOKEN+"\n"),
                            ("ota_url","http://example.test/x"),
                            ("websocket_url","wss://user:pass@example.test/x"),
                            ("websocket_url","wss://other.test/x")]:
            c=self.creds();c[field]=value
            with self.assertRaises(ValueError):provision(raw,c,"9c:13:9e:8a:c7:74")
        with self.assertRaises(ValueError):provision(raw,self.creds(),"00:00:00:00:00:00")

    def test_cli_private_exclusive_no_secret_output_and_wrong_mac(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); inp=root/"input.bin";creds=root/"credentials.json";out=root/"output.bin"
            inp.write_bytes(generate(self.fixture(),16384))
            creds.write_text(json.dumps(self.creds()));creds.chmod(0o600)
            args=[sys.executable,str(SCRIPTS/"provision_device_nvs.py"),
                  "--input",str(inp),"--credentials",str(creds),"--output",str(out),
                  "--expected-mac","9c:13:9e:8a:c7:74"]
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertNotIn(TOKEN,result.stdout+result.stderr)
            self.assertEqual(out.stat().st_mode&0o777,0o600)
            saved=out.read_bytes()
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(saved,out.read_bytes())
            other=root/"wrong.bin";args[args.index("--output")+1]=str(other);args[-1]="00:00:00:00:00:00"
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertFalse(other.exists())
            self.assertNotIn(TOKEN,result.stdout+result.stderr)

if __name__=="__main__":unittest.main()
