"""Read selected BNDR menu resources and catalogue non-texture CP932 candidates."""
import argparse
from collections import Counter
import importlib.util
import json
import re
import struct
from pathlib import Path
from bndr import read_index

spec=importlib.util.spec_from_file_location('cmp',Path(__file__).with_name('konami-cmp.py'))
cmp=importlib.util.module_from_spec(spec);spec.loader.exec_module(cmp)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path);p.add_argument('members',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();wanted={r['name'] for r in json.loads(a.members.read_text())}
    a.output.mkdir(parents=True,exist_ok=True);rows=[];chunks=[];kinds=Counter();done=0
    with a.archive.open('rb') as source:
        for entry in read_index(a.archive):
            if entry['name'] not in wanted:continue
            path=a.output/entry['name']
            if path.exists():data=path.read_bytes()
            else:
                source.seek(entry['offset']);data=source.read(entry['size'])
                if data.startswith(b'CMP\0'):data=cmp.decompress(data)
                path.write_bytes(data)
            done+=1
            if data[:4]!=b'CHK ':continue
            at=16
            while at+16<=len(data) and data[at:at+8]!=b'CHUNKEND':
                kind,flags,allocated,actual=struct.unpack_from('>4sIII',data,at)
                if allocated<16 or actual>allocated or at+allocated>len(data):raise ValueError('Invalid CHK extent')
                payload=data[at+16:at+16+actual];label=kind.decode('ascii','replace');kinds[label]+=1
                chunks.append(dict(member=entry['name'],kind=label,offset=at,size=actual,magic=payload[:16].hex()))
                # Bitmap/font/model data creates false CP932 strings.
                if not payload.startswith(b'X360SUR ') and not kind.startswith((b'FT',b'FN',b'MDL')):
                    offset=at+16
                    for block in payload.split(b'\0'):
                        if 4<=len(block)<=4096:
                            try:text=block.decode('cp932')
                            except UnicodeError:text=''
                            japanese=sum('\u3041'<=c<='\u30fa' or '\u3400'<=c<='\u9fff' for c in text)
                            if japanese>=2 and all(c.isprintable() or c in '\r\n\t' for c in text):
                                # Exclude halfwidth binary prefixes and glyph/codebook noise.
                                if not any('\uff61'<=c<='\uff9f' for c in text):
                                    rows.append(dict(member=entry['name'],kind=label,offset=offset,source=text))
                        offset+=len(block)+1
                at+=allocated
            if done%20==0:print(f'{done}/{len(wanted)} resources scanned',flush=True)
    (a.output/'strings.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (a.output/'chunks.json').write_text(json.dumps(chunks,indent=2),encoding='utf-8')
    print(f'{done} resources; {len(rows)} candidate strings; chunk kinds: {dict(kinds)}',flush=True)

if __name__=='__main__':main()
