"""Catalogue candidate CP932 strings in the loaded executable's .rdata section."""
import argparse
import csv
import struct
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--min-japanese', type=int, default=2)
    parser.add_argument('--pointer-targets', action='store_true', help='Include static string targets after non-NUL-terminated pointer tables')
    args = parser.parse_args()
    data = args.image.read_bytes()
    start, end, base = 0x400, 0xAAE0C + 0x400, 0x82000000
    if len(data) < end or data[:2] != b'MZ':
        parser.error('Expected the loaded-image.bin for the supported Pro Spirits 3 executable')
    rows, offset = [], start
    for block in data[start:end].split(b'\0'):
        if 2 <= len(block) <= 4096:
            try:
                text = block.decode('cp932')
                japanese = sum('\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in text)
                if japanese >= args.min_japanese and all(c.isprintable() or c in '\r\n\t\u3000' for c in text):
                    rows.append(dict(address=f'0x{base + offset:08X}', bytes=len(block), japanese=text, english=''))
            except UnicodeDecodeError:
                pass
        offset += len(block) + 1
    if args.pointer_targets:
        known={int(r['address'],0) for r in rows}
        targets=set()
        for lo,hi in [(0x400,end),(0x6e0000,0xc10ad8)]:
            targets.update(p[0] for p in struct.iter_unpack('>I',data[lo:hi-hi%4]) if base+start<=p[0]<base+end)
        for address in sorted(targets-known):
            at=address-base
            stop=data.find(b'\0',at,min(end,at+4097))
            if stop<0:continue
            block=data[at:stop]
            try:text=block.decode('cp932')
            except UnicodeDecodeError:continue
            japanese=sum('\u3040'<=c<='\u30ff' or '\u4e00'<=c<='\u9fff' for c in text)
            if 2<=len(block)<=4096 and japanese>=args.min_japanese and all(c.isprintable() or c in '\r\n\t\u3000' for c in text):
                rows.append(dict(address=f'0x{address:08X}',bytes=len(block),japanese=text,english=''))
        rows.sort(key=lambda r:int(r['address'],0))
    with args.output.open('x', newline='', encoding='utf-8-sig') as target:
        writer = csv.DictWriter(target, fieldnames=['address', 'bytes', 'japanese', 'english'])
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {len(rows)} candidate strings. Binary false positives require review.')


if __name__ == '__main__':
    main()
