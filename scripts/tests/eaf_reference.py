"""Independent strict reader for EAF 8-bit palette blocks; no optimizer imports."""
import struct


def huffman(data):
    size = int.from_bytes(data[:2], "little")
    dictionary, bits = data[2:2 + size], data[2 + size:]
    codes, pos = {}, 1
    while pos < len(dictionary):
        symbol, length = dictionary[pos:pos + 2]
        pos += 2
        n = (length + 7) // 8
        code = int.from_bytes(dictionary[pos:pos + n], "big")
        pos += n
        assert 1 <= length <= 64
        codes[(length, code)] = symbol
    assert pos == size and bits and 0 <= dictionary[0] <= 7
    result, code, length = bytearray(), 0, 0
    for bit in range(len(bits) * 8 - dictionary[0]):
        code = (code << 1) | ((bits[bit // 8] >> (7 - bit % 8)) & 1)
        length += 1
        if (length, code) in codes:
            result.append(codes[length, code])
            length, code = 0, 0
    assert length == 0
    return bytes(result)


def decode(data):
    assert data[:4] == b"\x89EAF"
    count, checksum, size = struct.unpack_from("<III", data, 4)
    assert size == len(data) - 16 and sum(data[16:]) & 0xffffffff == checksum
    frames, offset = [], 0
    for n in range(count):
        length, start = struct.unpack_from("<II", data, 16 + 8 * n)
        assert start == offset
        frame = data[16 + 8 * count + start:16 + 8 * count + start + length]
        assert frame[:12] == b"ZZ_S\0V1.00\0\x08"
        width, height, blocks, rows = struct.unpack_from("<HHHH", frame, 12)
        assert blocks == (height + rows - 1) // rows
        lengths = struct.unpack_from("<" + "I" * blocks, frame, 20)
        pos = 20 + 4 * blocks
        palette = frame[pos:pos + 1024]
        assert len(palette) == 1024
        pos += 1024
        pixels, encoded = bytearray(), []
        for k, block_length in enumerate(lengths):
            block = frame[pos:pos + block_length]
            assert len(block) == block_length and block
            payload = block[1:]
            if block[0] in (1, 3):
                payload = huffman(payload)
            if block[0] in (0, 1):
                assert len(payload) % 2 == 0
                indices = bytearray()
                for run, symbol in struct.iter_unpack("BB", payload):
                    assert run > 0
                    indices.extend(bytes([symbol]) * run)
            else:
                assert block[0] in (3, 5)
                indices = payload
            assert len(indices) == width * min(rows, height - rows * k)
            pixels.extend(indices)
            encoded.append(block)
            pos += block_length
        assert pos == len(frame)
        frames.append({"header": frame[:20], "palette": palette, "indices": bytes(pixels),
                       "blocks": encoded, "dimensions": (width, height)})
        offset += length
    assert 16 + 8 * count + offset == len(data)
    return frames
