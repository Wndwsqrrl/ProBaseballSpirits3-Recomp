"""Extract the supported image's 103 three-line newspaper headline records."""
import argparse
import csv
import json
import re
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();data=a.image.read_bytes();rows=[]
    for i in range(309):
        at=0x7e8708+i*41;raw=data[at:at+41]
        if len(raw)!=41 or b'\0' not in raw:raise ValueError('Invalid headline slot')
        source=raw.split(b'\0')[0].decode('cp932')
        if not all(c.isprintable() or c=='\u3000' for c in source):raise ValueError('Invalid headline text')
        if not source:continue
        # The game fills these display placeholders before rendering.
        pattern=re.sub('＋{2,}','%s',source)
        pattern=re.sub('＄{2,}','%d',pattern)
        rows.append(dict(address='0x00000000' if pattern!=source else f'0x{0x82000000+at:08X}',bytes=len(pattern.encode('cp932')),japanese=pattern,english=''))
    with a.output.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['address','bytes','japanese','english']);w.writeheader();w.writerows(rows)
    print(f'{len(rows)} newspaper lines and runtime patterns extracted.')

if __name__=='__main__':main()
