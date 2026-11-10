"""Derive family-name lookups from the game's own Japanese/jersey name records.

Does not infer given-name readings. Outputs English and fingerprints only.
"""
import argparse
from collections import defaultdict
import importlib.util
import json
from pathlib import Path
import re

spec=importlib.util.spec_from_file_location('full_text',Path(__file__).with_name('generate-full-text.py'))
full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--reviewed-roster',type=Path,action='append',default=[],
                   help='Use reviewed name fields from this file (repeatable)')
    p.add_argument('--name-readings',type=Path,help='Decoded in-game NAMEDIC dictionaries')
    p.add_argument('--patch-output',type=Path,help='Export bounded name-field patches outside reviewed Hanshin slots')
    a=p.parse_args();image=a.image.read_bytes();names=defaultdict(set);records=0
    reviewed={}
    for path in a.reviewed_roster:
        for row in json.loads(path.read_text(encoding='utf-8')):
            address=int(row['address'],0)
            if 'source_hash' in row:
                offset=address-0x82000000
                raw=image[offset:offset+row['slot_size']]
                if offset<0 or len(raw)!=15 or full.fnv64(raw)!=int(row['source_hash'],16):
                    raise ValueError(f'Reviewed source name differs at {address:#x}')
            if address in reviewed and reviewed[address]!=row['english']:
                raise ValueError(f'Conflicting reviewed name at {address:#x}')
            reviewed[address]=row['english']
    readings=defaultdict(set)
    if a.name_readings:
        for dictionary in json.loads(a.name_readings.read_text(encoding='utf-8')):
            for name,options in dictionary.items():readings[name].update(options)
    spec_kana=importlib.util.spec_from_file_location('kana',Path(__file__).with_name('kana-romaji.py'))
    kana=importlib.util.module_from_spec(spec_kana);spec_kana.loader.exec_module(kana)
    derived=0;patches=[];unresolved=[]
    for match in re.finditer(rb"[A-Z][A-Z .'-]{1,11}\0",image[0x6e0000:0xc10ad8]):
        at=0x6e0000+match.start();start=at-45;fields=[]
        for offset in (0,15,30):
            raw=image[start+offset:start+offset+15];end=raw.find(b'\0')
            if end<0 or any(raw[end:]):break
            try:text=raw[:end].decode('cp932')
            except UnicodeError:
                # A few given names use the game's FCxx gaiji extensions.
                # Keep their bytes for matching without inventing a Unicode reading.
                if offset!=15:break
                text=''
            if not all(c.isprintable() or c=='\u3000' for c in text):break
            fields.append((raw[:end],text))
        if len(fields)!=3 or not fields[0][1] or not any(ord(c)>127 for c in fields[0][1]):continue
        english=match.group()[:-1].decode().title();records+=1
        # One-kanji names also overlap ordinary labels such as West/Star.
        # Keep those context-sensitive cases out of global content lookups.
        if len(fields[0][1])>1:names[fields[0][0]].add(english)
        if fields[1][0]:
            # The lineup adds one given-name character to distinguish players.
            first=fields[1][0][:1 if fields[1][0][0]<0x80 else 2]
            names[fields[0][0]+first].add(english)
        if fields[2][1]:names[fields[2][0]].add(english)
        family=reviewed.get(0x82000000+start,english.split('.')[-1].strip())
        if fields[1][0]:
            first=fields[1][0][:1 if fields[1][0][0]<0x80 else 2]
            names[family.encode('ascii')+first].add(english)
        given=reviewed.get(0x82000000+start+15)
        if fields[1][0]:
            if not given and len(readings[fields[1][1]])==1:
                given=kana.romanize(next(iter(readings[fields[1][1]])))
                if given:derived+=1
            # Outside reviewed teams, use the game's Latin family name until
            # given-name readings are reviewed. Never guess kanji name readings.
            label=family+(' '+given if given else '')
            for separator in ('\u3000',' '):
                sep=separator.encode('cp932')
                names[fields[0][0]+sep+fields[1][0]].add(label)
                # Imported players sometimes display given name first.
                names[fields[1][0]+sep+fields[0][0]].add(label)
                names[family.encode('ascii')+sep+fields[1][0]].add(label)
        if not 0x8274EADC<=0x82000000+start<0x8275150C:
            for offset,label in ((0,family),(15,given),(30,english if fields[2][1] else None)):
                if not label or not label.isascii() or len(label)>=15:continue
                raw=image[start+offset:start+offset+15]
                patches.append(dict(address=f'0x{0x82000000+start+offset:08X}',record_address=f'0x{0x82000000+start:08X}',
                    slot_size=15,source_hash=f'{full.fnv64(raw):016X}',english=label))
        if fields[1][0] and not given:
            unresolved.append(dict(
                record_address=f'0x{0x82000000+start:08X}',
                family=family,
                source_given=fields[1][1],
                source_hex=fields[1][0].hex(),
                readings=sorted(readings[fields[1][1]]),
            ))
    result=[];ambiguous=0
    for original,options in sorted(names.items()):
        if len(options)!=1:ambiguous+=1;continue
        result.append(dict(address='0x00000000',source_size=len(original),
            source_hash=f'{full.fnv64(original):016X}',english=next(iter(options)),status='game-roster-family'))
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if a.patch_output:a.patch_output.write_text(json.dumps(patches,indent=2)+'\n',encoding='utf-8')
    (a.image.parent/'unresolved-name-readings.json').write_text(json.dumps(unresolved,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{records} structured records; {len(result)} family/display aliases; {derived} given names from unambiguous in-game readings; {ambiguous} ambiguous aliases left for review.')

if __name__=='__main__':main()
