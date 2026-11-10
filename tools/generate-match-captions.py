"""Recover the native match-caption patterns from a supported loaded image."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

IMAGE_BASE = 0x82000000
CAPTION_TABLE = 0x8282D6D8
CAPTION_COUNT = 39
CAPTION_SOURCE_HASH = '67125223310d7a73ae4892753ea51a5976475a1ec8e0219fb9f67961e7dd7797'

# The game leaves out zero hundredths and thousandths in Japanese averages.
# Put the omitted zeros back for the three-place English AVG.
AVERAGE_PATTERNS = (
    ('%d割', '.%d00'),
    ('%d割%d分', '.%d%d0'),
    ('%d割%d厘', '.%d0%d'),
    ('%d割%d分%d厘', '.%d%d%d'),
    ('１０割', '1.000'),
)


def generate(image, captions):
    start = CAPTION_TABLE - IMAGE_BASE
    table = image[start:start + CAPTION_COUNT * 8]

    def read_string(address):
        offset = address - IMAGE_BASE
        return image[offset:image.index(b'\0', offset, offset + 100) + 1]

    strings = [read_string(address) for (address,) in struct.iter_unpack('>I', table)]
    if hashlib.sha256(table + b''.join(strings)).hexdigest() != CAPTION_SOURCE_HASH:
        raise ValueError('Match-caption table differs from the supported loaded image')
    if len(captions) != CAPTION_COUNT or any(text.count('%d') != 1 for text in captions):
        raise ValueError('Expected one English numeric slot per native caption')

    rows = []
    for index, english in enumerate(captions):
        prefix, suffix = (value[:-1].decode('cp932') for value in strings[index * 2:index * 2 + 2])
        # These are the type ranges that the native number builder formats as AVG.
        is_average = index < 5 or 23 <= index <= 28
        patterns = AVERAGE_PATTERNS if is_average else (('%d', '%d'),)
        for source_number, english_number in patterns:
            rows.append({
                'address': '0x00000000',
                'source': prefix + source_number + suffix,
                'english': english.replace('%d', english_number),
                'status': 'reviewed',
            })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('captions', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    captions = json.loads(args.captions.read_text(encoding='utf-8'))
    rows = generate(args.image.read_bytes(), captions)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Generated {len(rows)} match-caption patterns and lookups.')


if __name__ == '__main__':
    main()
