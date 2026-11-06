"""Lossless EAF optimizer regression tests, offline with pinned official decoder."""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest
from eaf_reference import decode

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def fixture(values):
    palette = bytes((n % 256 for n in range(1024)))
    width, height, rows = 320, len(values) // 320, len(values) // 320
    raw = bytes(values)
    runs = bytearray()
    for v in raw:
        if runs and runs[-1] == v and runs[-2] < 255:
            runs[-2] += 1
        else:
            runs.extend((1, v))
    block = b"\0" + runs
    frame = b"ZZ_S\0V1.00\0\x08" + struct.pack("<HHHHI", width, height, 1, rows, len(block)) + palette + block
    table = struct.pack("<IIII", len(frame), 0, len(frame), len(frame))
    body = table + frame * 2
    return b"\x89EAF" + struct.pack("<III", 2, sum(body) & 0xffffffff, len(body)) + body


class OptimizerTests(unittest.TestCase):
    def setUp(self):
        import optimize_eaf
        self.optimize = optimize_eaf.optimize

    def check(self, source):
        result = self.optimize(source)
        self.assertLessEqual(len(result), len(source))
        self.assertEqual(result, self.optimize(source))
        self.assertEqual(result, self.optimize(result))
        for old, new in zip(decode(source), decode(result)):
            for field in ("header", "palette", "indices"):
                self.assertEqual(old[field], new[field])
        return result

    def test_rle_huffman_and_all_indices_alpha(self):
        source = fixture([i % 256 for i in range(5120)])
        result = self.check(source)
        self.assertLess(len(result), len(source))

    def test_single_symbol_and_255_runs(self):
        self.check(fixture([255] * 5120))

    def test_preserves_original_when_dictionary_cost_larger(self):
        source = fixture([0] * 640)
        self.assertEqual(self.check(source), source)

    def test_invalid_checksum_rejected(self):
        source = bytearray(fixture([0] * 5120))
        source[8] ^= 1
        with self.assertRaises((ValueError, AssertionError)):
            self.optimize(source)

    def test_manifest_covers_all_24_current_sources(self):
        import json
        import verify_eaf_assets as verifier
        manifest = json.loads((ROOT / verifier.MANIFEST).read_text())
        self.assertEqual(len(manifest["assets"]), 24)
        self.assertEqual({a["file"] for a in manifest["assets"]},
                         {p.name for p in (ROOT / verifier.ASSETS / "emoji_large").glob("*.eaf")})

    def test_changed_or_new_asset_never_bypasses_hash_and_official_decoder(self):
        from unittest.mock import patch
        import verify_eaf_assets as verifier
        read_bytes = Path.read_bytes
        for name in ("annoyed.eaf", "listening.eaf", "roast.eaf", "sulk.eaf"):
            def tamper(path):
                data = read_bytes(path)
                # Container stays decodable: mutate one unused palette alpha byte
                # and repair its checksum. Previously Python-only fallback passed.
                if path == ROOT / verifier.ASSETS / "emoji_large" / name:
                    data = bytearray(data)
                    count = struct.unpack_from("<I", data, 4)[0]
                    frame = 16 + count * 8
                    blocks = struct.unpack_from("<H", data, frame + 16)[0]
                    data[frame + 20 + blocks * 4 + 1023] ^= 1
                    struct.pack_into("<I", data, 8, sum(data[16:]) & 0xffffffff)
                    return bytes(data)
                return data
            with self.subTest(name=name), patch.object(Path, "read_bytes", tamper):
                with self.assertRaises(AssertionError):
                    verifier.verify(ROOT)

    def test_current_assets_preserve_manifest_frame_hashes(self):
        import verify_eaf_assets
        result = verify_eaf_assets.verify(ROOT)
        self.assertEqual(result["registrations"], 39)
        self.assertGreater(result["original_frames"], 0)


if __name__ == "__main__":
    unittest.main()
