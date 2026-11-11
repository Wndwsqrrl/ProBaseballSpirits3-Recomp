"""Build English renderer lookups for selectable announcer names in EDIT.CHK."""
import argparse
import json
import re
import struct
from pathlib import Path
from runpy import run_path


def read_announced_names(data):
    if data[:4] != b'CHK ' or struct.unpack_from('>I', data, 12)[0] != len(data):
        raise ValueError('Expected a decoded EDIT.CHK container')
    offset = 16
    while offset + 16 <= len(data) and data[offset:offset + 8] != b'CHUNKEND':
        kind, _, allocated, used = struct.unpack_from('>4sIII', data, offset)
        if allocated < 16 or used > allocated - 16 or offset + allocated > len(data):
            raise ValueError('Invalid EDIT.CHK chunk')
        if kind == b'VC00':
            break
        offset += allocated
    else:
        raise ValueError('Missing announced-name chunk')
    start = offset + 16
    payload = data[start:start + used]
    if payload[:12] != b'LITTUGU ' + b'\xff' * 4 or payload[-1:] != b'\xff':
        raise ValueError('Invalid announced-name table header')
    count = struct.unpack_from('<I', payload, 12)[0]
    table_end = 16 + count * 8
    if count == 0 or table_end >= len(payload) - 1:
        raise ValueError('Invalid announced-name table size')
    entries = list(struct.iter_unpack('<II', payload[16:table_end]))
    if entries[0][0] != table_end:
        raise ValueError('Invalid announced-name data start')
    records, seen_ids, seen_text = [], set(), set()
    for index, (position, voice_id) in enumerate(entries):
        end = entries[index + 1][0] if index + 1 < count else len(payload) - 1
        if not table_end <= position < end <= len(payload) - 1:
            raise ValueError('Invalid announced-name record bounds')
        field = payload[position:end]
        source = field.rstrip(b'\0')
        if (not source or not field.endswith(b'\0') or b'\0' in source
                or not 0x00400000 <= voice_id <= 0x0040FFFF
                or voice_id in seen_ids or source in seen_text):
            raise ValueError('Invalid or duplicate announced-name record')
        seen_ids.add(voice_id)
        seen_text.add(source)
        records.append((f'{voice_id:08X}', start + position, source))
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('edit_chk', type=Path)
    parser.add_argument('spellings', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    romanize = run_path(str(Path(__file__).with_name('kana-romaji.py')))['romanize']
    spellings = json.loads(args.spellings.read_text(encoding='utf-8'))
    records = read_announced_names(args.edit_chk.read_bytes())
    if set(spellings) - {voice_id for voice_id, _, _ in records}:
        raise ValueError('A reviewed spelling has no matching audio ID')
    rows = []
    fingerprints = set()
    labels = set()
    for voice_id, offset, source in records:
        kana = source.decode('cp932')
        if not re.fullmatch(r'[\u3041-\u3096ー]+', kana):
            raise ValueError(f'Unexpected announced-name characters for {voice_id}')
        english = spellings.get(voice_id, romanize(kana))
        if not english or not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", english):
            raise ValueError(f'Invalid announced-name spelling for {voice_id}')
        if english.casefold() in labels:
            raise ValueError(f'Duplicate display name for {voice_id}: {english}')
        labels.add(english.casefold())
        fingerprint = 0xcbf29ce484222325
        for byte in source:
            fingerprint = ((fingerprint ^ byte) * 0x100000001b3) & 0xffffffffffffffff
        if fingerprint in fingerprints:
            raise ValueError(f'Announced-name fingerprint collision at {offset:#x}')
        fingerprints.add(fingerprint)
        rows.append(f'    {{0x{fingerprint:016X}ULL, "{english}"}},')
    header = [
        '// Generated from the announced-name table in EDIT.CHK.',
        '#pragma once',
        '#include <cstdint>',
        '#include <string_view>',
        '',
        'struct AnnouncedName { uint64_t source_hash; std::string_view english; };',
        'inline constexpr AnnouncedName kAnnouncedNames[] = {',
        *rows,
        '};',
        '',
    ]
    args.output.write_bytes('\n'.join(header).encode('ascii'))
    print(f'{len(rows)} announced names, {len(spellings)} spelling overrides.')


if __name__ == '__main__':
    main()
