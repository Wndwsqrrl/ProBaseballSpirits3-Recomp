"""Export unmatched renderer-trace prose for the draft translation pipeline."""
import argparse
import csv
import re
import unicodedata
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audit',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();rows=[]
    for line in a.audit.read_text(encoding='utf-8-sig').splitlines():
        fields=line.split('\t')
        if len(fields)<2 or fields[1]!='unknown':continue
        source=bytes.fromhex(fields[0]).decode('cp932')
        # Width-only name separators/numbers are handled by runtime normalization.
        if not re.search(r'[\u3041-\u30fa\u3400-\u9fff]',unicodedata.normalize('NFKC',source)):continue
        rows.append(dict(address='0x00000000',bytes=len(source.encode('cp932')),japanese=source,english=''))
    with a.output.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['address','bytes','japanese','english']);writer.writeheader();writer.writerows(rows)
    print(f'{len(rows)} unmatched prose runs exported.')

if __name__=='__main__':main()
