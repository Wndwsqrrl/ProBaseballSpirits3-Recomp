"""Build a separate extracted-disc tree with localized interface assets.

The original extracted disc is read only. Unchanged files are hard links;
baseball.fbd is rebuilt as a separate file, with updated sector offsets.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from bndr import read_index
from pennant_events import MEMBER as PENNANT_MEMBER, patch_titles

spec = importlib.util.spec_from_file_location('konami_cmp', Path(__file__).with_name('konami-cmp.py'))
cmp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cmp)


def patch_chk(data, atlases, font_path, preview):
    if data.startswith(b'CMP\0'):
        data = cmp.decompress(data)
    if data[:4] != b'CHK ' or struct.unpack_from('>I', data, 12)[0] != len(data):
        raise ValueError('Invalid CHK container')
    patched, found, position = bytearray(data), set(), 16
    while position + 16 <= len(data):
        if data[position:position+8] == b'CHUNKEND':
            break
        kind, flags, allocated, actual = struct.unpack_from('>4sIII', data, position)
        if not 16 <= allocated or actual > allocated or position + allocated > len(data):
            raise ValueError('Invalid CHK chunk extent')
        payload = position + 16
        if data[payload:payload+8] == b'X360SUR ':
            name = data[payload+16:payload+48].split(b'\0')[0].decode('ascii')
            if name in atlases:
                width, height = struct.unpack_from('>II', data, payload+48)
                raw_start, raw_size = payload + 100, actual - 101
                pixel_format = data[payload+68:payload+72].hex()
                if pixel_format not in ('1828014f', '18280143', '1a200152'):
                    raise ValueError(f'Unsupported atlas pixel format: {name}')
                raw = data[raw_start:raw_start+raw_size]
                if pixel_format == '1a200152':
                    if raw_size != width * height // 2:
                        raise ValueError('Invalid BC1 atlas extent')
                    swapped = b''.join(raw[i:i+2][::-1] for i in range(0,len(raw),2))
                    image = Image.frombytes('RGBA',(width,height),swapped,'bcn',(1,'DXT1'))
                else:
                    if raw_size != width * height * 2:
                        raise ValueError('Invalid 16-bit atlas extent')
                    rgba = bytearray(width * height * 4)
                    for index, (pixel,) in enumerate(struct.iter_unpack('>H', raw)):
                        if pixel_format == '18280143':
                            value=(((pixel>>10)&31)*255//31,((pixel>>5)&31)*255//31,(pixel&31)*255//31,255 if pixel&0x8000 else 0)
                        else:
                            value=(((pixel>>8)&15)*17,((pixel>>4)&15)*17,(pixel&15)*17,((pixel>>12)&15)*17)
                        rgba[index*4:index*4+4] = bytes(value)
                    image = Image.frombytes('RGBA', (width, height), bytes(rgba))
                dirty_blocks=set()
                for label in atlases[name]:
                    x, y, w, h = label['rect']
                    if not 0 <= x < x+w <= width or not 0 <= y < y+h <= height:
                        raise ValueError('Label rectangle outside atlas')
                    scale = 4
                    tile = Image.new('RGBA', (w*scale, h*scale), tuple(label.get('background',(68,68,68,0))))
                    draw = ImageDraw.Draw(tile)
                    for size in range(38, 12, -1):
                        font = ImageFont.truetype(str(font_path), size*scale)
                        box = draw.textbbox((0,0), label['text'], font=font)
                        if box[2]-box[0] <= (w-label.get('padding',12))*scale and box[3]-box[1] <= (h-3)*scale:
                            break
                    x_text = (w*scale - (box[2]-box[0]))/2 - box[0]
                    y_text = (h*scale - (box[3]-box[1]))/2 - box[1]
                    draw.text((x_text, y_text), label['text'], font=font,
                        fill=tuple(label.get('foreground',(255,255,255,255))),
                        stroke_width=label.get('outline_width',0)*scale,
                        stroke_fill=tuple(label.get('outline',(0,0,0,255))))
                    tile = tile.resize((w,h), Image.Resampling.LANCZOS)
                    image.paste(tile, (x,y))
                    dirty_blocks.update((bx,by) for by in range(y//4,(y+h+3)//4) for bx in range(x//4,(x+w+3)//4))
                encoded = bytearray(raw)
                if pixel_format == '1a200152':
                    # Position glyphs are white masks tinted by the game. Keep
                    # every untouched compressed block byte-identical.
                    for bx,by in dirty_blocks:
                        indices=0
                        for py in range(4):
                            for px in range(4):
                                red,green,blue,alpha=image.getpixel((bx*4+px,by*4+py))
                                if alpha>=128 and max(red,green,blue)-min(red,green,blue)>8:
                                    raise ValueError('BC1 mask encoder supports grayscale glyphs only')
                                index=3 if alpha<128 else (1 if red>=192 else 2 if red>=64 else 0)
                                indices |= index << (2*(py*4+px))
                        block=struct.pack('<HHI',0,0xFFFF,indices)
                        block=b''.join(block[i:i+2][::-1] for i in range(0,8,2))
                        start=(by*(width//4)+bx)*8
                        encoded[start:start+8]=block
                else:
                    for index, (red,green,blue,alpha) in enumerate(image.getdata()):
                        if pixel_format == '18280143':
                            pixel = ((1 if alpha>=128 else 0)<<15) | ((red>>3)<<10) | ((green>>3)<<5) | (blue>>3)
                        else:
                            pixel = ((alpha>>4)<<12) | ((red>>4)<<8) | ((green>>4)<<4) | (blue>>4)
                        struct.pack_into('>H', encoded, index*2, pixel)
                patched[raw_start:raw_start+raw_size] = encoded
                preview.mkdir(parents=True, exist_ok=True)
                image.save(preview / (name + '.english.png'))
                found.add(name)
        position += allocated
    if found != set(atlases):
        raise ValueError(f'Atlas names not found: {set(atlases)-found}')
    return bytes(patched)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game_root', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--labels', required=True, type=Path)
    parser.add_argument('--pennant-events', type=Path, help='Reviewed Pennant event titles')
    parser.add_argument('--font', type=Path, default=Path('C:/Windows/Fonts/ARIALNB.TTF'))
    parser.add_argument('--preview', required=True, type=Path)
    args = parser.parse_args()
    source, output = args.game_root.resolve(), args.output.resolve()
    if source == output or source in output.parents or output in source.parents:
        parser.error('Source and output must be separate, non-nested directories')
    archive = source / 'cdvdroot/baseball.fbd'
    entries = read_index(archive)
    labels = json.loads(args.labels.read_text(encoding='utf-8'))
    members = set(labels)
    titles = None
    if args.pennant_events:
        if PENNANT_MEMBER in members:
            parser.error(f'{PENNANT_MEMBER} is reserved for event titles')
        members.add(PENNANT_MEMBER)
        titles = json.loads(args.pennant_events.read_text(encoding='utf-8'))
        if not isinstance(titles, list):
            parser.error('Pennant titles must be a list')
    missing = members - {entry['name'] for entry in entries}
    if missing:
        raise ValueError(f'Archive members missing: {missing}')
    patches = {}
    with archive.open('rb') as stream:
        for entry in entries:
            name = entry['name']
            if name not in members:
                continue
            stream.seek(entry['offset'])
            data = stream.read(entry['size'])
            if name in labels:
                patches[name] = patch_chk(data, labels[name], args.font, args.preview)
            else:
                if data.startswith(b'CMP\0'):
                    data = cmp.decompress(data)
                patches[name] = patch_titles(data, titles)
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'cdvdroot/baseball.fbd'
    if target.exists() and os.path.samefile(archive, target):
        raise ValueError('Output archive is linked to the original; refusing to write')
    for path in source.rglob('*'):
        if not path.is_file() or path == archive:
            continue
        destination = output / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            try:
                os.link(path, destination)
            except OSError:
                # exFAT and some external drives do not support hard links.
                shutil.copy2(path, destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.building')
    table_size = (16 + 268*len(entries) + 2047) // 2048 * 2048
    directory, sector = bytearray(table_size), table_size // 2048
    struct.pack_into('>4sIII', directory, 0, b'BNDR', 2048, sector, len(entries))
    with archive.open('rb') as stream, temporary.open('xb') as destination:
        destination.write(directory)
        for index, entry in enumerate(entries):
            data = patches.get(entry['name'])
            size = len(data) if data is not None else entry['size']
            allocated = (size + 2047) // 2048 * 2048
            record = 16 + index*268
            name = entry['name'].encode('ascii')
            directory[record:record+len(name)] = name
            struct.pack_into('>III', directory, record+256, sector, size, allocated)
            if data is not None:
                destination.write(data)
            else:
                stream.seek(entry['offset'])
                remaining = size
                while remaining:
                    block = stream.read(min(remaining, 1024*1024))
                    if not block:
                        raise ValueError('Truncated source archive')
                    destination.write(block)
                    remaining -= len(block)
            destination.write(bytes(allocated-size))
            sector += allocated // 2048
        destination.seek(0)
        destination.write(directory)
    rebuilt = read_index(temporary)
    with temporary.open('rb') as stream:
        for entry in rebuilt:
            if entry['name'] in patches:
                stream.seek(entry['offset'])
                if hashlib.sha256(stream.read(entry['size'])).digest() != hashlib.sha256(patches[entry['name']]).digest():
                    raise ValueError('Rebuilt member verification failed')
    os.replace(temporary, target)
    print(f'Built {output}: {len(patches)} localized archive members, {sum(len(v) for v in labels.values())} atlases.', flush=True)


if __name__ == '__main__':
    main()
