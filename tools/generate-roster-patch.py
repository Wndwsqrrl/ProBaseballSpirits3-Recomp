"""Generate bounded team-name patches; source bytes are represented by hashes."""
import argparse
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('input',type=Path)
parser.add_argument('output',type=Path)
parser.add_argument('--image',type=Path)
args=parser.parse_args()
rows=json.loads(args.input.read_text(encoding='utf-8'))
image=args.image.read_bytes() if args.image else None
seen=set()
lines=['// Generated from reviewed team roster slots.','#pragma once',
       '#include <cstdint>','#include <string_view>',
       'struct RosterNamePatch { uint32_t address, size; uint64_t hash; std::string_view english; };',
       'inline constexpr RosterNamePatch kHanshinNames[] = {']
for row in rows:
    encoded=row['english'].encode('ascii')
    address=int(row['address'],0)
    if row['slot_size']!=15 or len(encoded)>=15 or b'\0' in encoded:
        raise ValueError('Name exceeds fixed roster field')
    if not 0x8274EADC<=address<0x8275150C or (address-0x8274EADC)%200 not in (0,15,30):
        raise ValueError('Name outside Hanshin record range')
    if address in seen:
        raise ValueError('Duplicate roster field')
    seen.add(address)
    if image is not None:
        raw=image[address-0x82000000:address-0x82000000+15]
        value=0xCBF29CE484222325
        for byte in raw:value=((value^byte)*0x100000001B3)&0xFFFFFFFFFFFFFFFF
        if len(raw)!=15 or value!=int(row['source_hash'],16):
            raise ValueError('Original roster fingerprint differs')
    lines.append(f'  {{{row["address"]}, {row["slot_size"]}, 0x{row["source_hash"]}ULL, "{row["english"]}"}},')
lines.append('};\n')
target=args.output;target.parent.mkdir(parents=True,exist_ok=True)
target.write_text('\n'.join(lines),encoding='utf-8')
print(f'Generated {len(rows)} bounded Hanshin name patches.')
