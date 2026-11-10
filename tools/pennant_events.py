"""Extract fixed-width fields from the supported Pennant event resource."""
import argparse
import hashlib
import json
from pathlib import Path
import re


MEMBER = 'PEMDFIX.CHK'
SOURCE_SHA256 = 'aab3299b3ac9b869c29508be56591d433d45f04017335e05f6b7f081e1b6feaa'
EVENT_COUNT = 187
CONTROL = re.compile(r'@.?')
# Each PEMD chunk holds one column. The final byte is a separate sentinel.
FIELDS = (
    ('reward', 0x20, 37),
    ('success_story', 0x1B40, 429),
    ('goal', 0x154B0, 45),
    ('goal_detail', 0x175A0, 143),
    ('failure_story', 0x1DE30, 391),
    ('introduction', 0x2FBE0, 391),
    ('failure_notice', 0x41990, 25),
    ('success_notice', 0x42BF0, 41),
    ('objective', 0x44A00, 37),
    ('title', 0x46520, 24),
)


def validate_source(data):
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError(f'Unsupported decoded {MEMBER} resource')


def load_translations(title_path, text_path):
    fields = {}
    if title_path:
        titles = json.loads(title_path.read_text(encoding='utf-8'))
        if not isinstance(titles, list) or len(titles) != EVENT_COUNT or any(title is None for title in titles):
            raise ValueError(f'Expected {EVENT_COUNT} Pennant event titles')
        fields['title'] = titles
    if text_path:
        additional = json.loads(text_path.read_text(encoding='utf-8'))
        if not isinstance(additional, dict) or 'title' in additional:
            raise ValueError('Pennant text must be an object of non-title fields')
        fields.update(additional)
    return fields


def patch_text(data, fields):
    validate_source(data)
    unknown = fields.keys() - {field for field, _, _ in FIELDS}
    if unknown:
        raise ValueError(f'Unknown Pennant text fields: {sorted(unknown)}')
    patched = bytearray(data)
    for field, start, width in FIELDS:
        if field not in fields:
            continue
        rows = fields[field]
        if not isinstance(rows, list) or len(rows) != EVENT_COUNT:
            raise ValueError(f'Expected {EVENT_COUNT} entries in Pennant field {field}')
        for index, text in enumerate(rows):
            if text is None:
                continue
            label = f'event {index + 1} {field}'
            if not isinstance(text, str) or not text.strip() or not all(' ' <= c <= '~' for c in text):
                raise ValueError(f'Invalid English text for {label}')
            encoded = text.encode('ascii')
            if len(encoded) >= width:
                raise ValueError(f'English text exceeds {width - 1} bytes for {label}')
            offset = start + index * width
            original = data[offset:offset + width].split(b'\0', 1)[0].decode('cp932')
            if not original or CONTROL.findall(original) != CONTROL.findall(text):
                raise ValueError(f'Empty source or changed control sequence for {label}')
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
