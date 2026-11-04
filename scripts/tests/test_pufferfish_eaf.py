"""Independent container/RLE decoding checks for the offline EAF encoder."""
import collections
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "encode_pufferfish_eaf.py"


def decode(data):
    """Test reader deliberately uses no encoder internals."""
    assert data[:4] == b"\x89EAF"
    frames, checksum, length = struct.unpack_from("<III", data, 4)
    assert length == len(data) - 16
    assert checksum == sum(data[16:]) & 0xffffffff
    result = []
    end = 0
    for n in range(frames):
        size, offset = struct.unpack_from("<II", data, 16 + n * 8)
        assert offset == end
        start = 16 + frames * 8 + offset
        frame = data[start:start + size]
        assert len(frame) == size
        assert frame[:12] == b"ZZ_S\0V1.00\0\x08"
        width, height, blocks, block_height = struct.unpack_from("<HHHH", frame, 12)
        assert blocks == (height + block_height - 1) // block_height
        lengths = struct.unpack_from("<" + "I" * blocks, frame, 20)
        pos = 20 + 4 * blocks
        palette_bytes = frame[pos:pos + 1024]
        assert len(palette_bytes) == 1024
        palette = [(r, g, b, a) for b, g, r, a in struct.iter_unpack("BBBB", palette_bytes)]
        assert all(c[3] == 255 for c in palette)
        pos += 1024
        pixels = []
        encoded_blocks = []
        for k, block_len in enumerate(lengths):
            block = frame[pos:pos + block_len]
            assert len(block) == block_len and block[0] == 0
            assert (len(block) - 1) % 2 == 0
            indices = []
            for count, index in struct.iter_unpack("BB", block[1:]):
                assert count > 0
                indices.extend([index] * count)
            assert len(indices) == width * min(block_height, height - k * block_height)
            pixels.extend(palette[index][:3] for index in indices)
            encoded_blocks.append(block)
            pos += block_len
        assert pos == size
        result.append((pixels, encoded_blocks, (width, height), frame))
        end += size
    assert 16 + frames * 8 + end == len(data)
    return result


class EafTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "offline encoder not implemented")
        spec = importlib.util.spec_from_file_location("pufferfish_encoder", SCRIPT)
        self.encoder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.encoder)

    def test_default_dimensions_and_duplicate_static_frames(self):
        parsed = decode(self.encoder.encode_image(Image.new("RGB", (320, 240), "red")))
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0], parsed[1])
        self.assertEqual(parsed[0][2], (320, 240))
        self.assertEqual(collections.Counter(parsed[0][0]), {(255, 0, 0): 76800})

    def test_reject_wrong_dimensions(self):
        with self.assertRaisesRegex(ValueError, "320.*240"):
            self.encoder.encode_image(Image.new("RGB", (240, 320)))

    def test_rle_splits_at_255_and_handles_tail_block(self):
        parsed = decode(self.encoder.encode_image(Image.new("RGB", (260, 3), "blue"), size=(260, 3), block_height=2))[0]
        self.assertEqual(parsed[1][0][1::2], bytes((255, 255, 10)))
        self.assertEqual(parsed[1][1][1::2], bytes((255, 5)))
        self.assertEqual(parsed[0], [(0, 0, 255)] * 780)

    def test_alpha_is_composited_over_black_before_quantizing(self):
        image = Image.new("RGBA", (4, 1))
        image.putdata([(255, 100, 50, 0), (200, 100, 50, 128), (255, 0, 0, 255), (0, 255, 0, 255)])
        pixels = decode(self.encoder.encode_image(image, size=(4, 1)))[0][0]
        self.assertEqual(pixels, [(0, 0, 0), (100, 50, 25), (255, 0, 0), (0, 255, 0)])

    def test_all_256_palette_colors_and_counts_roundtrip(self):
        colors = [(n, (n * 13) % 256, 255 - n) for n in range(256)]
        image = Image.new("RGB", (256, 3))
        image.putdata(colors * 3)
        pixels = decode(self.encoder.encode_image(image, size=image.size, block_height=2))[0][0]
        self.assertEqual(pixels, colors * 3)
        self.assertEqual(collections.Counter(pixels), collections.Counter(colors * 3))

    def test_more_than_256_colors_is_quantized(self):
        image = Image.new("RGB", (320, 240))
        image.putdata([((x * 7) % 256, (x // 320) % 256, x % 256) for x in range(76800)])
        pixels = decode(self.encoder.encode_image(image))[0][0]
        self.assertLessEqual(len(set(pixels)), 256)
        self.assertEqual(len(pixels), 76800)

    def test_invalid_block_heights_rejected(self):
        for block_height in (0, -1, 65536):
            with self.subTest(block_height=block_height), self.assertRaises(ValueError):
                self.encoder.encode_image(Image.new("RGB", (320, 240)), block_height=block_height)

    def test_batch_24_pngs_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / "source", Path(tmp) / "output"
            source.mkdir()
            for n in range(24):
                Image.new("RGB", (320, 240), (n, 0, 0)).save(source / f"emote_{n:02}.png")
            manifest = self.encoder.encode_directory(source, output, expected_count=24)
            self.assertEqual(len(list(output.glob("*.eaf"))), 24)
            self.assertEqual(json.loads((output / "metadata.json").read_text()), manifest)
            self.assertEqual(len(manifest["assets"]), 24)
            for asset in manifest["assets"]:
                self.assertLessEqual(len(asset["file"].encode("utf-8")), 31)
                self.assertEqual(len(decode((output / asset["file"]).read_bytes())), 2)
                self.assertEqual(len(asset["sha256"]), 64)

    def test_batch_wrong_count_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            with self.assertRaisesRegex(ValueError, "24"):
                self.encoder.encode_directory(source, Path(tmp) / "out", expected_count=24)
            self.assertFalse((Path(tmp) / "out").exists())

    def test_batch_rejects_32_byte_filename_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            Image.new("RGB", (320, 240)).save(source / ("x" * 28 + ".png"))
            with self.assertRaisesRegex(ValueError, "31"):
                self.encoder.encode_directory(source, Path(tmp) / "out")
            self.assertFalse((Path(tmp) / "out").exists())


if __name__ == "__main__":
    unittest.main()
