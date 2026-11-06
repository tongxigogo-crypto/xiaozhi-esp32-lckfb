#!/usr/bin/env python3
"""Deterministic lossless EAF 8-bit palette optimizer; Python standard library only.

Uses official esp_emote_gfx 3.0.5 types 0/1/3. Never changes frame headers,
palette bytes, pixel indices, count or order. Dictionary overhead participates
in block selection; ties retain the input block. No resizing or quantization.
"""
import argparse
from collections import Counter
import heapq
from pathlib import Path
import struct


def encode_huffman(data):
    heap = [(count, symbol, symbol) for symbol, count in sorted(Counter(data).items())]
    heapq.heapify(heap)
    serial = 256
    while len(heap) > 1:
        a, b = heapq.heappop(heap), heapq.heappop(heap)
        heapq.heappush(heap, (a[0] + b[0], serial, (a[2], b[2])))
        serial += 1
    codes = {}
    def visit(node, code, length):
        if isinstance(node, int):
            codes[node] = (code, max(length, 1))
        else:
            visit(node[0], code << 1, length + 1)
            visit(node[1], (code << 1) | 1, length + 1)
    visit(heap[0][2], 0, 0)
    if max(length for code, length in codes.values()) > 64:
        return None
    dictionary, bits = bytearray([0]), bytearray()
    for symbol, (code, length) in sorted(codes.items()):
        dictionary.extend((symbol, length))
        dictionary.extend(code.to_bytes((length + 7) // 8, "big"))
    pending, count = 0, 0
    for symbol in data:
        code, length = codes[symbol]
        pending = (pending << length) | code
        count += length
        while count >= 8:
            count -= 8
            bits.append((pending >> count) & 255)
        pending &= (1 << count) - 1
    if count:
        bits.append(pending << (8 - count))
        dictionary[0] = 8 - count
    return struct.pack("<H", len(dictionary)) + dictionary + bits


def decode_huffman(data):
    size = int.from_bytes(data[:2], "little")
    table, stream = data[2:2 + size], data[2 + size:]
    if not table or not stream:
        raise ValueError("optimizer requires an explicit Huffman bit stream")
    tree, pos = {}, 1
    while pos < size:
        symbol, length = table[pos:pos + 2]
        pos += 2
        n = (length + 7) // 8
        code = int.from_bytes(table[pos:pos + n], "big")
        pos += n
        node = tree
        for shift in range(length - 1, -1, -1):
            node = node.setdefault((code >> shift) & 1, {})
        node["symbol"] = symbol
    output, node = bytearray(), tree
    for k in range(len(stream) * 8 - table[0]):
        node = node[(stream[k // 8] >> (7 - k % 8)) & 1]
        if "symbol" in node:
            output.append(node["symbol"])
            node = tree
    if node is not tree:
        raise ValueError("incomplete Huffman code")
    return bytes(output)


def rle_encode(indices):
    runs = bytearray()
    for symbol in indices:
        if runs and runs[-1] == symbol and runs[-2] < 255:
            runs[-2] += 1
        else:
            runs.extend((1, symbol))
    return bytes(runs)


def optimize(data):
    if data[:4] != b"\x89EAF" or len(data) < 24:
        raise ValueError("not EAF")
    count, checksum, size = struct.unpack_from("<III", data, 4)
    if size != len(data) - 16 or sum(data[16:]) & 0xffffffff != checksum:
        raise ValueError("invalid EAF size/checksum")
    frames, expected_offset = [], 0
    for n in range(count):
        length, offset = struct.unpack_from("<II", data, 16 + 8 * n)
        if offset != expected_offset:
            raise ValueError("noncontiguous frame table")
        start = 16 + 8 * count + offset
        frame = data[start:start + length]
        if frame[:12] != b"ZZ_S\0V1.00\0\x08":
            raise ValueError("only V1.00 8-bit palette frames supported")
        width, height, blocks, rows = struct.unpack_from("<HHHH", frame, 12)
        if not rows or blocks != (height + rows - 1) // rows:
            raise ValueError("invalid block geometry")
        lengths = struct.unpack_from("<" + "I" * blocks, frame, 20)
        pos = 20 + 4 * blocks + 1024
        prefix = frame[20 + 4 * blocks:pos]
        if len(prefix) != 1024:
            raise ValueError("truncated palette")
        out_blocks = []
        for k, block_length in enumerate(lengths):
            block = frame[pos:pos + block_length]
            pos += block_length
            if not block or len(block) != block_length:
                raise ValueError("truncated block")
            payload = block[1:]
            if block[0] in (1, 3):
                payload = decode_huffman(payload)
            if block[0] in (0, 1):
                if len(payload) % 2 or any(run == 0 for run in payload[::2]):
                    raise ValueError("invalid RLE")
                indices = b"".join(bytes([symbol]) * run for run, symbol in struct.iter_unpack("BB", payload))
                runs = payload
            elif block[0] in (3, 5):
                indices = payload
                runs = rle_encode(indices)
            else:
                raise ValueError("unsupported block encoding")
            if len(indices) != width * min(rows, height - k * rows):
                raise ValueError("wrong decoded block size")
            candidates = [block, b"\0" + runs]
            for kind, raw in ((1, runs), (3, indices)):
                encoded = encode_huffman(raw)
                if encoded is not None:
                    candidates.append(bytes([kind]) + encoded)
            out_blocks.append(min(candidates, key=len))
        if pos != len(frame):
            raise ValueError("trailing frame bytes")
        frames.append(frame[:20] + struct.pack("<" + "I" * blocks, *(len(b) for b in out_blocks)) + prefix + b"".join(out_blocks))
        expected_offset += length
    if 16 + 8 * count + expected_offset != len(data):
        raise ValueError("trailing container bytes")
    table, offset = bytearray(), 0
    for frame in frames:
        table.extend(struct.pack("<II", len(frame), offset))
        offset += len(frame)
    body = table + b"".join(frames)
    return b"\x89EAF" + struct.pack("<III", count, sum(body) & 0xffffffff, len(body)) + body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    source = args.source.read_bytes()
    result = optimize(source)
    args.destination.write_bytes(result)
    print(f"{len(source)} -> {len(result)} bytes")


if __name__ == "__main__":
    main()
