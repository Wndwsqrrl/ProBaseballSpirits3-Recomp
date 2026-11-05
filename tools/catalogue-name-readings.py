"""Decode the game's NAMEDIC kana-to-name dictionaries; keep readings local."""
import argparse
from collections import defaultdict
import json
import struct
from pathlib import Path

def decode_dictionary(data):
    if data[:8]!=b'NAMEDIC ':raise ValueError('Expected NAMEDIC')
    result=defaultdict(set)
    def word(at):
        if not 0<=at<=len(data)-4:raise ValueError('Dictionary offset out of bounds')
        return struct.unpack_from('<I',data,at)[0]
    def string(at):
        end=data.find(b'\0',at)
        if end<0:raise ValueError('Unterminated dictionary string')
        return data[at:end],end+1
    def kana(codes):
        return b''.join(b'\x81\x5b' if code==84 else bytes((0x82,code+0x9e)) for code in codes if code).decode('cp932')
    def record(at,prefix):
        variants=word(at);ending,at=string(at+4)
        reading=kana([*prefix,*ending])
        if variants>10000:raise ValueError('Invalid variant count')
        for _ in range(variants):
            raw,at=string(at);name=raw.decode('cp932')
            result[name].add(reading)
    visited=set()
    def walk(node,prefix):
        if node in visited:raise ValueError('Dictionary node cycle/alias')
        visited.add(node)
        kind=word(node)
        if kind==0:
            for code in range(85):
                target=word(node+4+code*4)
                if target:
                    if code==0:record(target,prefix)
                    else:walk(target,prefix+[code])
        elif kind==1:
            count=word(node+4)
            if count>10000:raise ValueError('Invalid dictionary group count')
            for i in range(count):
                record(word(node+8+i*4),prefix)
        else:raise ValueError(f'Unknown dictionary node kind {kind}')
    walk(12,[])
    return {name:sorted(readings) for name,readings in result.items()}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('edit_chk',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();data=a.edit_chk.read_bytes();at=16;out=[]
    while at+16<=len(data) and data[at:at+8]!=b'CHUNKEND':
        kind,flags,allocated,actual=struct.unpack_from('>4sIII',data,at)
        if allocated<16 or actual>allocated or at+allocated>len(data):raise ValueError('Invalid CHK')
        if kind==b'NM00':out.append(decode_dictionary(data[at+16:at+16+actual]))
        at+=allocated
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Decoded dictionaries:',[len(x) for x in out])

if __name__=='__main__':main()
