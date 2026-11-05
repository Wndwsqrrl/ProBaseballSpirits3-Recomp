"""Generate bounded roster fields derived from Latin jerseys and NAMEDIC."""
import argparse
import json
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('header',type=Path);p.add_argument('--image',type=Path)
    a=p.parse_args();rows=json.loads(a.input.read_text(encoding='utf-8'));image=a.image.read_bytes() if a.image else None;seen=set()
    lines=['#pragma once','#include <cstdint>','#include <string_view>',
        'struct AllRosterNamePatch {uint32_t address,size;uint64_t hash;std::string_view english;};',
        'inline constexpr AllRosterNamePatch kAllRosterNames[]={']
    for r in rows:
        address=int(r['address'],0);record=int(r['record_address'],0);value=r['english'].encode('ascii')
        if not 0x82740000<=record<0x82770000 or address-record not in (0,15,30):raise ValueError('Invalid roster field')
        if 0x8274EADC<=address<0x8275150C:raise ValueError('Reviewed Hanshin slots must remain separate')
        if r['slot_size']!=15 or not value or len(value)>=15 or b'\0' in value or address in seen:raise ValueError('Invalid bounded name')
        seen.add(address)
        if image:
            raw=image[address-0x82000000:address-0x82000000+15];h=0xcbf29ce484222325
            for b in raw:h=((h^b)*0x100000001b3)&0xffffffffffffffff
            if h!=int(r['source_hash'],16):raise ValueError('Source name hash mismatch')
        lines.append(f'  {{{r["address"]},15,0x{r["source_hash"]}ULL,"{r["english"]}"}},')
    lines.append('};\n');a.header.parent.mkdir(parents=True,exist_ok=True)
    a.header.write_text('\n'.join(lines),encoding='utf-8');print(f'{len(rows)} bounded roster fields generated.')

if __name__=='__main__':main()
