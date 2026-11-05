"""Inspect Konami BNDR archives; extract selected members without altering the source."""
import argparse
import csv
import struct
from pathlib import Path


def read_index(path):
    archive_size = path.stat().st_size
    with path.open('rb') as source:
        header = source.read(16)
        if len(header) != 16:
            raise ValueError('Truncated BNDR header')
        magic, alignment, table_sectors, count = struct.unpack('>4sIII', header)
        if magic != b'BNDR' or alignment != 2048 or not 0 < count <= 100000:
            raise ValueError('Unsupported BNDR header')
        table_end = table_sectors * alignment
        if 16 + count * 268 > table_end or table_end > archive_size:
            raise ValueError('Invalid BNDR directory extent')
        records = source.read(count * 268)
    if len(records) != count * 268:
        raise ValueError('Truncated BNDR directory')
    entries, names = [], set()
    for index in range(count):
        record = records[index * 268:(index + 1) * 268]
        name = record[:256].split(b'\0', 1)[0].decode('ascii')
        sector, size, allocated = struct.unpack_from('>III', record, 256)
        offset = sector * alignment
        if not name or name in ('.', '..') or any(c in name for c in '/\\:'):
            raise ValueError('Unsafe BNDR member name')
        if name.upper() in names:
            raise ValueError('Duplicate BNDR member name')
        names.add(name.upper())
        if size > allocated or allocated % alignment or offset < table_end or offset + allocated > archive_size:
            raise ValueError(f'Invalid BNDR member extent: {name}')
        entries.append(dict(name=name, offset=offset, size=size, allocated=allocated))
    ordered = sorted(entries, key=lambda e: e['offset'])
    for previous, current in zip(ordered, ordered[1:]):
        if previous['offset'] + previous['allocated'] > current['offset']:
            raise ValueError('Overlapping BNDR members')
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--index', type=Path, help='Write CSV index')
    parser.add_argument('--extract', nargs='+', default=[], metavar='MEMBER')
    parser.add_argument('--output', type=Path, help='New directory for selected members')
    args = parser.parse_args()
    entries = read_index(args.archive)
    if args.index:
        with args.index.open('x', newline='', encoding='utf-8') as target:
            writer = csv.DictWriter(target, fieldnames=['name', 'offset', 'size', 'allocated'])
            writer.writeheader()
            writer.writerows(entries)
    if args.extract:
        by_name = {entry['name']: entry for entry in entries}
        if not args.output or args.output.exists():
            parser.error('--output must name a new directory')
        missing = set(args.extract) - by_name.keys()
        if missing:
            parser.error(f'Unknown members: {sorted(missing)}')
        args.output.mkdir(parents=True)
        with args.archive.open('rb') as source:
            for name in dict.fromkeys(args.extract):
                entry = by_name[name]
                source.seek(entry['offset'])
                with (args.output / name).open('xb') as target:
                    remaining = entry['size']
                    while remaining:
                        block = source.read(min(remaining, 1024 * 1024))
                        if not block:
                            raise ValueError('Archive changed or truncated during extraction')
                        target.write(block)
                        remaining -= len(block)
    print(f'Validated {len(entries)} members; extracted {len(set(args.extract))}.')


if __name__ == '__main__':
    main()
