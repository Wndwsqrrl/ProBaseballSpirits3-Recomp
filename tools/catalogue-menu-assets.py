"""Inventory selected CHK menu resources and make texture contact sheets locally."""
import argparse
import importlib.util
import json
import struct
from pathlib import Path
from PIL import Image, ImageDraw
from bndr import read_index

spec=importlib.util.spec_from_file_location('cmp',Path(__file__).with_name('konami-cmp.py'))
cmp=importlib.util.module_from_spec(spec);spec.loader.exec_module(cmp)

def decode(raw,w,h,fmt):
    if fmt in ('1a200152','1a200153','1a200154'):
        swapped=b''.join(raw[i:i+2][::-1] for i in range(0,len(raw),2))
        codec={'1a200152':(1,'DXT1'),'1a200153':(2,'DXT3'),'1a200154':(3,'DXT5')}[fmt]
        return Image.frombytes('RGBA',(w,h),swapped,'bcn',codec)
    if fmt not in ('1828014f','18280143'):return None
    rgba=bytearray()
    for p, in struct.iter_unpack('>H',raw):
        if fmt=='1828014f':rgba.extend(((p>>8&15)*17,(p>>4&15)*17,(p&15)*17,(p>>12&15)*17))
        else:rgba.extend(((p>>10&31)*255//31,(p>>5&31)*255//31,(p&31)*255//31,255 if p&0x8000 else 0))
    return Image.frombytes('RGBA',(w,h),bytes(rgba))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path);p.add_argument('output',type=Path);p.add_argument('members',nargs='+')
    a=p.parse_args();entries={r['name']:r for r in read_index(a.archive)}
    if set(a.members)-entries.keys():p.error('Unknown archive member')
    a.output.mkdir(parents=True,exist_ok=True);rows=[];previews=[]
    with a.archive.open('rb') as archive:
        for member in a.members:
            target=a.output/member
            if target.exists():data=target.read_bytes()
            else:
                r=entries[member];archive.seek(r['offset']);data=archive.read(r['size'])
                if data.startswith(b'CMP\0'):data=cmp.decompress(data)
                target.write_bytes(data)
            if data[:4]!=b'CHK ':continue
            at=16
            while at+16<=len(data) and data[at:at+8]!=b'CHUNKEND':
                kind,flags,allocated,actual=struct.unpack_from('>4sIII',data,at)
                if allocated<16 or actual>allocated or at+allocated>len(data):raise ValueError('Invalid chunk extent')
                payload=at+16
                if data[payload:payload+8]==b'X360SUR ':
                    name=data[payload+16:payload+48].split(b'\0')[0].decode('ascii')
                    w,h=struct.unpack_from('>II',data,payload+48);fmt=data[payload+68:payload+72].hex()
                    row=dict(member=member,name=name,w=w,h=h,format=fmt,offset=payload+100,size=actual-101)
                    rows.append(row)
                    if w*h<=1024*1024:
                        im=decode(data[row['offset']:row['offset']+row['size']],w,h,fmt)
                        if im:
                            im.save(a.output/(member+'-'+name+'.png'));previews.append((row,im))
                at+=allocated
            print(member,'inventoried',flush=True)
    (a.output/'textures.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    for start in range(0,len(previews),24):
        sheet=Image.new('RGB',(1200,6*180),(60,60,60));draw=ImageDraw.Draw(sheet)
        for index,(row,im) in enumerate(previews[start:start+24]):
            x=(index%4)*300;y=(index//4)*180
            draw.text((x+3,y+2),row['member']+' / '+row['name'],fill='white')
            copy=im.copy();copy.thumbnail((294,150));sheet.paste(copy,(x+3,y+23),copy)
        sheet.save(a.output/f'contact-{start//24:02d}.png')
    print(f'{len(rows)} texture records; {len(previews)} decoded previews.')

if __name__=='__main__':main()
