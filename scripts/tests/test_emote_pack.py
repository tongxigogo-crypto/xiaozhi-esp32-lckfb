"""Detect the actual 16-byte font truncation failure using the mmap format."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("pack",ROOT/"scripts/verify_emote_pack.py")
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)

def fixture(width):
    index={"text_font":pack.FONT,"emoji_collection":[{"file":"idle.eaf"}],"layout":[]}
    entries=[(pack.FONT,b"font"),("idle.eaf",b"frame"),("index.json",json.dumps(index).encode())]
    table=bytearray();payload=bytearray()
    for name,data in entries:
        table.extend(name.encode()[:width].ljust(width,b"\0"))
        table.extend(struct.pack("<III",len(data),len(payload),0))
        payload.extend(b"ZZ"+data)
    return struct.pack("<III",len(entries),0,len(payload))+table+payload

class EmotePackTests(unittest.TestCase):
    def test_16_byte_real_format_rejects_truncated_font(self):
        with self.assertRaisesRegex(ValueError,"missing/truncated filenames.*font_puhui_common_20_4.bin"):
            pack.verify(fixture(16),16)

    def test_32_byte_real_format_preserves_full_font_and_references(self):
        result=pack.verify(fixture(32),32)
        self.assertEqual(result["missing"],[])
        self.assertEqual(result["references"],2)

    def test_board_producer_and_reader_filename_width_covers_font(self):
        self.assertGreaterEqual(pack.board_name_length(),len(pack.FONT.encode())+1)
