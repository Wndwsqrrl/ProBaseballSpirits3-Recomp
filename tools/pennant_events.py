"""Extract fixed-width fields from the supported Pennant event resource."""
import argparse
import hashlib
import json
from pathlib import Path


MEMBER = 'PEMDFIX.CHK'
SOURCE_SHA256 = 'aab3299b3ac9b869c29508be56591d433d45f04017335e05f6b7f081e1b6feaa'
EVENT_COUNT = 187
# Each PEMD chunk holds one column. The final byte is a separate sentinel.
FIELDS = (
    ('reward', 0x20, 37),
    ('introduction', 0x1B40, 429),
    ('goal', 0x154B0, 45),
    ('goal_detail', 0x175A0, 143),
    ('success_story', 0x1DE30, 391),
    ('failure_story', 0x2FBE0, 391),
    ('failure_notice', 0x41990, 25),
    ('success_notice', 0x42BF0, 41),
    ('objective', 0x44A00, 37),
    ('title', 0x46520, 24),
)


def validate_source(data):
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError(f'Unsupported decoded {MEMBER} resource')


def patch_titles(data, titles):
    validate_source(data)
    if not isinstance(titles, list) or len(titles) != EVENT_COUNT:
        raise ValueError(f'Expected {EVENT_COUNT} Pennant event titles')
    _, start, width = FIELDS[-1]
    patched = bytearray(data)
    for index, title in enumerate(titles):
        if not isinstance(title, str) or not title or not all(' ' <= c <= '~' for c in title):
            raise ValueError(f'Invalid English title for event {index + 1}')
        encoded = title.encode('ascii')
        if len(encoded) >= width:
            raise ValueError(f'English title exceeds {width - 1} bytes for event {index + 1}')
        offset = start + index * width
        patched[offset:offset + width] = (encoded + b'\0').ljust(width, b'\xcd')
    return bytes(patched)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Decoded PEMDFIX.CHK')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = args.source.read_bytes()
    validate_source(data)
    events = []
    for index in range(EVENT_COUNT):
        event = {'event': index + 1}
        for field, start, width in FIELDS:
            offset = start + index * width
            event[field] = data[offset:offset + width].split(b'\0', 1)[0].decode('cp932')
        events.append(event)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(events, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(f'Extracted {len(events)} Pennant events.')


if __name__ == '__main__':
    main()
