"""Verify unchanged archive members and bytes outside localized atlas regions."""
import argparse
import importlib.util
import json
import struct
from pathlib import Path
from bndr import read_index
from pennant_events import MEMBER as PENNANT_MEMBER, load_translations, patch_text
from txcpack_text import load_packed_text, patch_packed_text

spec=importlib.util.spec_from_file_location('cmp',Path(__file__).with_name('konami-cmp.py'))
cmp=importlib.util.module_from_spec(spec);spec.loader.exec_module(cmp)

def verify_member(original,patched,atlases):
    if original.startswith(b'CMP\0'):original=cmp.decompress(original)
    if len(original)!=len(patched):raise ValueError('Decoded member size changed')
    allowed=bytearray(len(original));at=16;found=set()
    while at+16<=len(original) and original[at:at+8]!=b'CHUNKEND':
        kind,flags,allocated,actual=struct.unpack_from('>4sIII',original,at)
        if allocated<16 or at+allocated>len(original):raise ValueError('Invalid chunk')
        payload=at+16
        if original[payload:payload+8]==b'X360SUR ':
            name=original[payload+16:payload+48].split(b'\0')[0].decode('ascii')
            if name in atlases:
                found.add(name);w,h=struct.unpack_from('>II',original,payload+48);fmt=original[payload+68:payload+72].hex();raw=payload+100
                regions = [label['rect'] for label in atlases[name]]
                regions.extend(label['clear_rect'] for label in atlases[name] if 'clear_rect' in label)
                for x,y,width,height in regions:
                    if not 0<=x<x+width<=w or not 0<=y<y+height<=h:raise ValueError('Invalid label bounds')
                    if fmt in ('1a200152','1a200153','1a200154'):
                        block_size = 8 if fmt == '1a200152' else 16
                        for by in range(y//4,(y+height+3)//4):
                            for bx in range(x//4,(x+width+3)//4):
                                start=raw+(by*(w//4)+bx)*block_size;allowed[start:start+block_size]=b'\1'*block_size
                    elif fmt in ('1828014f','18280143','18280186'):
                        stride = 4 if fmt == '18280186' else 2
                        for row in range(y,y+height):
                            start=raw+(row*w+x)*stride;allowed[start:start+width*stride]=b'\1'*(width*stride)
                    else:raise ValueError('Unsupported verification format')
        at+=allocated
    if found!=set(atlases):raise ValueError('Missing localized atlas')
    for i,(a,b) in enumerate(zip(original,patched)):
        if a!=b and not allowed[i]:raise ValueError(f'Unexpected change at decoded byte {i:#x}')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('original',type=Path);p.add_argument('english',type=Path)
    p.add_argument('--labels',required=True,type=Path);p.add_argument('--report',required=True,type=Path)
    p.add_argument('--pennant-events',type=Path,help='Reviewed Pennant event titles')
    p.add_argument('--pennant-text',type=Path,help='Reviewed Pennant event fields')
    p.add_argument('--packed-text',type=Path,help='Reviewed TXCPACK text slots')
    a=p.parse_args();labels=json.loads(a.labels.read_text(encoding='utf-8'))
    packed = load_packed_text(a.packed_text)
    localized = labels.keys() | packed.keys()
    pennant = load_translations(a.pennant_events, a.pennant_text)
    if pennant and PENNANT_MEMBER in localized:
        p.error('Pennant event text uses a separate archive member')
    old=read_index(a.original);new={x['name']:x for x in read_index(a.english)}
    if set(new)!={x['name'] for x in old}:raise ValueError('Archive membership changed')
    if localized - new.keys():raise ValueError('Localized members missing from archive')
    if pennant and PENNANT_MEMBER not in new:
        raise ValueError(f'Archive member missing: {PENNANT_MEMBER}')
    preserved=0
    with a.original.open('rb') as source,a.english.open('rb') as target:
        for i,entry in enumerate(old):
            other=new[entry['name']];source.seek(entry['offset']);target.seek(other['offset'])
            if entry['name'] in localized:
                data = source.read(entry['size'])
                if data.startswith(b'CMP\0'):
                    data = cmp.decompress(data)
                if entry['name'] in packed:
                    data = patch_packed_text(data, packed[entry['name']])
                verify_member(data,target.read(other['size']),labels.get(entry['name'], {}))
            elif pennant and entry['name'] == PENNANT_MEMBER:
                data = source.read(entry['size'])
                if data.startswith(b'CMP\0'):
                    data = cmp.decompress(data)
                if target.read(other['size']) != patch_text(data, pennant):
                    raise ValueError('Pennant event text differs from expected bytes')
            else:
                if entry['size']!=other['size']:raise ValueError('Unchanged member size differs')
                remaining=entry['size']
                while remaining:
                    count=min(remaining,1024*1024)
                    if source.read(count)!=target.read(count):raise ValueError('Unchanged member bytes differ')
                    remaining-=count
                preserved+=1
            if (i+1)%400==0:print(f'{i+1}/{len(old)} members verified',flush=True)
    result=dict(archive_members=len(old),unchanged_members_verified=preserved,localized_members=sorted(localized),
        atlases=sum(len(x) for x in labels.values()),labels=sum(len(v) for x in labels.values() for v in x.values()),
        outside_localized_regions_unchanged=True)
    if packed:
        result['packed_text_slots'] = sum(map(len, packed.values()))
    if pennant:
        result['localized_members'].append(PENNANT_MEMBER)
        result['localized_members'].sort()
        if 'title' in pennant:
            result['pennant_event_titles'] = len(pennant['title'])
        additional = {field: sum(text is not None for text in rows)
                      for field, rows in pennant.items() if field != 'title'}
        if additional:
            result['pennant_event_fields'] = additional
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
