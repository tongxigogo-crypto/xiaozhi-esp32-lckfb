#!/usr/bin/env python3
"""Offline PNG -> EAF draft encoder (Pillow required).

Format reference: Espressif's gfx_eaf_dec.c / .h, retrieved 2026-11-05:
https://github.com/espressif2022/esp_emote_gfx/tree/master/src/lib/eaf
Only the 8-bit palette, split-block RLE subset is emitted. The uint32 checksum
is a sum of body bytes, NOT CRC32. Each static image is stored twice because
the firmware adapter plays total_frames - 1. No resizing or asset promotion.

Example (default requires 24 PNGs, each 320x240):
  python scripts/encode_pufferfish_eaf.py INPUT_DIRECTORY OUTPUT_DIRECTORY
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image


def _rle(indices):
    """Encode nonempty palette indices as nonzero count/value pairs."""
    result = bytearray((0,))  # EAF_DEC_ENCODING_RLE
    value, count = indices[0], 0
    for index in indices:
        if index != value or count == 255:
            result.extend((count, value))
            value, count = index, 0
        count += 1
    result.extend((count, value))
    return bytes(result)


def encode_image(image, *, size=(320, 240), block_height=16):
    """Return two identical complete static frames in an EAF container.

    RGBA is composited onto opaque black before deterministic median-cut
    quantization. Every BGRA palette entry is opaque, including unused entries.
    """
    width, height = size
    if not (1 <= width <= 65535 and 1 <= height <= 65535):
        raise ValueError("width and height must fit nonzero uint16")
    if image.size != size:
        raise ValueError(f"expected {width}x{height} PNG, got {image.width}x{image.height}")
    if not 1 <= block_height <= 65535:
        raise ValueError("block_height must fit nonzero uint16")
    block_count = (height + block_height - 1) // block_height
    # The decoder stores its data_offset in uint16, including the palette.
    if 18 + 4 * block_count + 1024 > 65535:
        raise ValueError("too many blocks for decoder uint16 data_offset")
    rgba = image.convert("RGBA")
    rgb = Image.alpha_composite(Image.new("RGBA", size, (0, 0, 0, 255)), rgba).convert("RGB")
    indexed = rgb.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    colors = indexed.getpalette()
    colors = colors + [0] * (768 - len(colors))
    palette = bytearray()
    for offset in range(0, 768, 3):
        r, g, b = colors[offset:offset + 3]
        palette.extend((b, g, r, 255))
    indices = indexed.tobytes()
    block_size = width * block_height
    blocks = [_rle(indices[pos:pos + block_size]) for pos in range(0, len(indices), block_size)]
    frame = (b"\x5a\x5a_S\0V1.00\0" + struct.pack("<BHHHH", 8, width, height, block_count, block_height)
             + struct.pack("<" + "I" * block_count, *(len(block) for block in blocks))
             + bytes(palette) + b"".join(blocks))
    table = struct.pack("<IIII", len(frame), 0, len(frame), len(frame))
    body = table + frame + frame
    return b"\x89EAF" + struct.pack("<III", 2, sum(body) & 0xffffffff, len(body)) + body


def encode_directory(input_dir, output_dir, *, size=(320, 240), block_height=16, expected_count=None):
    """Validate the entire PNG batch before writing EAF drafts and metadata."""
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if not input_dir.is_dir():
        raise ValueError(f"input directory does not exist: {input_dir}")
    paths = sorted((p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"), key=lambda p: p.name)
    if expected_count is not None and len(paths) != expected_count:
        raise ValueError(f"expected {expected_count} PNGs, found {len(paths)}")
    if not paths:
        raise ValueError("no PNG files found")
    pending = []
    names = set()
    for path in paths:
        name = path.stem + ".eaf"
        # mmap assets use a 32-byte filename field; reserve one byte for NUL.
        if len(name.encode("utf-8")) > 31:
            raise ValueError(f"EAF filename exceeds 31 UTF-8 bytes: {name}")
        if name.casefold() in names:
            raise ValueError(f"duplicate output filename: {name}")
        names.add(name.casefold())
        with Image.open(path) as image:
            if image.format != "PNG":
                raise ValueError(f"not a PNG image: {path.name}")
            encoded = encode_image(image, size=size, block_height=block_height)
        pending.append((path, name, encoded))
    manifest = {
        "format": "EAF", "encoder": "pufferfish-offline-rle-v1", "status": "draft",
        "width": size[0], "height": size[1], "block_height": block_height,
        "frame_count": 2, "visible_frames": 1, "bit_depth": 8,
        "background": "black", "palette_order": "BGRA", "palette_alpha": 255,
        "checksum": "uint32_le_sum_of_body_bytes", "assets": [],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for source, name, encoded in pending:
        (output_dir / name).write_bytes(encoded)
        manifest["assets"].append({
            "source": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "file": name, "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest(),
        })
    (output_dir / "metadata.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--block-height", type=int, default=16)
    parser.add_argument("--expected-count", type=int, default=24)
    args = parser.parse_args()
    try:
        manifest = encode_directory(args.input_dir, args.output_dir, size=(args.width, args.height),
                                    block_height=args.block_height, expected_count=args.expected_count)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Encoded {len(manifest['assets'])} PNGs into EAF drafts in {args.output_dir}")


if __name__ == "__main__":
    main()
