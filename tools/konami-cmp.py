"""Decode the CMP/L/HS LZSS variant observed in Pro Spirits 3 menu assets.

Derived from the game's decoder at 0x825D3D48: a zeroed 4096-byte ring,
LSB-first flags (1 = reference), and dictionary writes at output_index - 18.
"""
import argparse
import struct
from pathlib import Path


def decompress(data):
    if len(data) < 18 or data[:8] != b'CMP\0L\0\0B' or data[12:14] != b'HS':
        raise ValueError('Unsupported CMP wrapper; expected CMP/L/B with HS stream')
    expected = struct.unpack_from('<I', data, 8)[0]
    stream_size = struct.unpack_from('>I', data, 14)[0]
    if expected != stream_size or not 0 < expected <= 64 * 1024 * 1024:
        raise ValueError('Invalid or inconsistent decoded length')
    ring, output, cursor = bytearray(4096), bytearray(), 18

    def next_byte():
        nonlocal cursor
        if cursor >= len(data):
            raise ValueError('Truncated CMP stream')
        value = data[cursor]
        cursor += 1
        return value

    while len(output) < expected:
        flags = next_byte()
        for bit in range(8):
            if len(output) == expected:
                break
            position = len(output)
            if flags & (1 << bit):
                low, high = next_byte(), next_byte()
                offset = low | ((high & 0xF0) << 4)
                count = (high & 0x0F) + 3
                if position + count > expected:
                    raise ValueError('CMP reference exceeds declared decoded size')
                for index in range(count):
                    value = ring[(position + offset + index) & 4095]
                    ring[(position - 18 + index) & 4095] = value
                    output.append(value)
            else:
                value = next_byte()
                ring[(position - 18) & 4095] = value
                output.append(value)
    return bytes(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    decoded = decompress(args.source.read_bytes())
    with args.output.open('xb') as target:
        target.write(decoded)
    print(f'Decoded {len(decoded)} bytes; signature {decoded[:4]!r}.')


if __name__ == '__main__':
    main()
