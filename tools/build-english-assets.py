"""Build a separate extracted-disc tree with localized interface assets.

The original extracted disc is read only. Unchanged files are hard links;
baseball.fbd is rebuilt as a separate file, with updated sector offsets.
"""
import argparse
from collections import deque
import hashlib
import io
import math
import importlib.util
import json
import os
import shutil
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from bndr import read_index
from pennant_events import MEMBER as PENNANT_MEMBER, load_translations, patch_text
from txcpack_text import load_packed_text, patch_packed_text

spec = importlib.util.spec_from_file_location('konami_cmp', Path(__file__).with_name('konami-cmp.py'))
cmp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cmp)


def block_has_color(image, bx, by):
    for y in range(by*4,by*4+4):
        for x in range(bx*4,bx*4+4):
            red,green,blue,alpha = image.getpixel((x,y))
            if alpha>=128 and max(red,green,blue)-min(red,green,blue)>8:
                return True
    return False


def read_caption_reference(data, name, expected_hash):
    """Read the original companion photo, before any labels are applied."""
    at = 16
    while at + 16 <= len(data) and data[at:at+8] != b'CHUNKEND':
        _, _, allocated, actual = struct.unpack_from('>4sIII', data, at)
        if allocated < 16 or actual > allocated or at + allocated > len(data):
            raise ValueError('Invalid caption-reference chunk')
        payload = at + 16
        if (data[payload:payload+8] == b'X360SUR '
                and data[payload+16:payload+48].split(b'\0')[0].decode('ascii') == name):
            width, height = struct.unpack_from('>II', data, payload+48)
            raw = data[payload+100:payload+actual-1]
            if (data[payload+68:payload+72].hex() != '1a200152'
                    or len(raw) != width * height // 2
                    or hashlib.sha256(raw).hexdigest() != expected_hash):
                raise ValueError('Caption reference differs from the reviewed BC1 photo')
            swapped = b''.join(raw[i:i+2][::-1] for i in range(0, len(raw), 2))
            return Image.frombytes('RGBA', (width, height), swapped, 'bcn', (1, 'DXT1'))
        at += allocated
    raise ValueError(f'Missing original caption-reference photo: {name}')


def restore_photo_caption(image, reference, options, label_rect):
    """Remove old white caption glyphs using the companion photo and local pixels."""
    if image.size != reference.size:
        raise ValueError('Caption photos must have identical dimensions')
    def mask_for(photo, rect):
        x, y, w, h = rect
        if not 0 <= x < x+w <= photo.width or not 0 <= y < y+h <= photo.height:
            raise ValueError('Caption cleanup rectangle outside photo')
        mask = Image.new('L', photo.size)
        pixels = mask.load()
        for py in range(y, y+h):
            for px in range(x, x+w):
                r, g, b, a = photo.getpixel((px, py))
                if min(r, g, b) >= 170 and max(r, g, b)-min(r, g, b) <= 85 and a >= 128:
                    pixels[px, py] = 255
        return mask.filter(ImageFilter.MaxFilter(9))
    target_mask = mask_for(image, options['erase_rect'])
    reference_mask = mask_for(reference, options['reference_erase_rect'])
    bounds = target_mask.getbbox()
    x, y, w, h = label_rect
    if bounds and not (x <= bounds[0] < bounds[2] <= x+w and y <= bounds[1] < bounds[3] <= y+h):
        raise ValueError('Caption glyph cleanup must remain inside its label rectangle')
    result = image.copy()
    pending = set()
    if bounds:
        for py in range(bounds[1], bounds[3]):
            for px in range(bounds[0], bounds[2]):
                if target_mask.getpixel((px, py)):
                    if reference_mask.getpixel((px, py)):
                        pending.add((px, py))
                    else:
                        result.putpixel((px, py), reference.getpixel((px, py)))
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    wave = deque((px, py) for px, py in sorted(pending)
                 if any((px+dx, py+dy) not in pending for dx, dy in directions))
    while wave:
        px, py = wave.popleft()
        if (px, py) not in pending:
            continue
        neighbors = [(px+dx, py+dy) for dx, dy in directions
                     if 0 <= px+dx < image.width and 0 <= py+dy < image.height
                     and (px+dx, py+dy) not in pending]
        if not neighbors:
            continue
        values = [result.getpixel(point) for point in neighbors]
        result.putpixel((px, py), tuple(round(sum(v[c] for v in values)/len(values)) for c in range(4)))
        pending.remove((px, py))
        wave.extend((px+dx, py+dy) for dx, dy in directions if (px+dx, py+dy) in pending)
    if pending:
        raise ValueError('Caption cleanup could not resolve overlapping glyphs')
    return result


def draw_rotated_label(tile, label, font_path, scale):
    rotation = label['text_rotation']
    if rotation not in (90, 270):
        return draw_angled_label(tile, label, font_path, scale)
    width, height = tile.height, tile.width
    stroke = label.get('outline_width', 0) * scale
    measure = ImageDraw.Draw(Image.new('L', (1, 1)))
    width_limit = width - label.get('padding', 12) * scale
    fit_limit = width_limit / label.get('min_width_ratio', 0.55) if label.get('condense') else width_limit
    for size in range(label.get('max_font_size', 38), label.get('min_font_size', 13)-1, -1):
        font = ImageFont.truetype(str(font_path), size * scale)
        box = measure.textbbox((0, 0), label['text'], font=font, stroke_width=stroke)
        if box[2]-box[0] <= fit_limit and box[3]-box[1] <= height-3*scale:
            break
    else:
        raise ValueError(f"Rotated English label does not fit {label['rect']}: {label['text']}")
    size = (math.ceil(box[2]-box[0]), math.ceil(box[3]-box[1]))
    transpose = Image.Transpose.ROTATE_270 if rotation == 90 else Image.Transpose.ROTATE_90
    layers = ([(stroke, label.get('outline', (0, 0, 0, 255)))] if stroke else [])
    layers.append((0, label.get('foreground', (255, 255, 255, 255))))
    for line_width, color in layers:
        mask = Image.new('L', size)
        ImageDraw.Draw(mask).text((-box[0], -box[1]), label['text'], font=font,
                                 fill=255, stroke_width=line_width, stroke_fill=255)
        if mask.width > width_limit:
            mask = mask.resize((int(width_limit), mask.height), Image.Resampling.LANCZOS)
        mask = mask.transpose(transpose)
        # A coverage mask also supports dark newspaper text cut out of opaque alpha.
        tile.paste(tuple(color), ((tile.width-mask.width)//2, (tile.height-mask.height)//2), mask)
    return tile


def draw_angled_label(tile, label, font_path, scale):
    rotation = label['text_rotation']
    if not isinstance(rotation, (int, float)) or not math.isfinite(rotation):
        raise ValueError('Text rotation must be a finite number of clockwise degrees')
    stroke = label.get('outline_width', 0) * scale
    measure = ImageDraw.Draw(Image.new('L', (1, 1)))
    width_limit = tile.width - label.get('padding', 12) * scale
    height_limit = tile.height - label.get('vertical_padding', 3) * scale
    polygon_mask = None
    if 'edit_polygon' in label:
        polygon_mask = Image.new('L', tile.size)
        ImageDraw.Draw(polygon_mask).polygon(
            [(px*scale, py*scale) for px, py in label['edit_polygon']], fill=255)
    for size in range(label.get('max_font_size', 38), label.get('min_font_size', 13)-1, -1):
        font = ImageFont.truetype(str(font_path), size * scale)
        box = measure.textbbox((0, 0), label['text'], font=font, stroke_width=stroke)
        mask = Image.new('L', (math.ceil(box[2]-box[0]), math.ceil(box[3]-box[1])))
        ImageDraw.Draw(mask).text((-box[0], -box[1]), label['text'], font=font,
                                 fill=255, stroke_width=stroke, stroke_fill=255)
        mask = mask.rotate(-rotation, Image.Resampling.BICUBIC, expand=True)
        if mask.width <= width_limit and mask.height <= height_limit:
            if polygon_mask is not None:
                placed = Image.new('L', tile.size)
                placed.paste(mask, ((tile.width-mask.width)//2, (tile.height-mask.height)//2))
                outside = ImageChops.subtract(placed, polygon_mask)
                if outside.point(lambda value: 255 if value > 16 else 0).getbbox():
                    continue
            break
    else:
        raise ValueError(f"Angled English label does not fit {label['rect']}: {label['text']}")
    layers = ([(stroke, label.get('outline', (0, 0, 0, 255)))] if stroke else [])
    layers.append((0, label.get('foreground', (255, 255, 255, 255))))
    for line_width, color in layers:
        ink = Image.new('L', (math.ceil(box[2]-box[0]), math.ceil(box[3]-box[1])))
        ImageDraw.Draw(ink).text((-box[0], -box[1]), label['text'], font=font,
                                fill=255, stroke_width=line_width, stroke_fill=255)
        ink = ink.rotate(-rotation, Image.Resampling.BICUBIC, expand=True)
        tile.paste(tuple(color), ((tile.width-ink.width)//2, (tile.height-ink.height)//2), ink)
    return tile


def draw_glowing_label(tile, label, font_path, scale):
    radius = label['glow_radius'] * scale
    if not 0 < radius <= 16 * scale:
        raise ValueError('Glow radius must be greater than zero and at most 16 pixels')
    margin = math.ceil(radius * 3)
    width_limit = tile.width - margin * 2 - label.get('padding', 12) * scale
    height_limit = tile.height - margin * 2 - 3 * scale
    fit_limit = width_limit / label.get('min_width_ratio', 0.55) if label.get('condense') else width_limit
    stroke = label.get('outline_width', 0) * scale
    measure = ImageDraw.Draw(Image.new('L', (1, 1)))
    for size in range(label.get('max_font_size', 38), label.get('min_font_size', 13)-1, -1):
        font = ImageFont.truetype(str(font_path), size * scale)
        box = measure.textbbox((0, 0), label['text'], font=font, stroke_width=stroke,
                              align=label.get('align', 'center'))
        if box[2]-box[0] <= fit_limit and box[3]-box[1] <= height_limit:
            break
    else:
        raise ValueError(f"Glowing English label does not fit {label['rect']}: {label['text']}")
    mask = Image.new('L', (math.ceil(box[2]-box[0]), math.ceil(box[3]-box[1])))
    ImageDraw.Draw(mask).text((-box[0], -box[1]), label['text'], font=font,
                             fill=255, stroke_width=stroke, stroke_fill=255,
                             align=label.get('align', 'center'))
    if mask.width > width_limit:
        mask = mask.resize((int(width_limit), mask.height), Image.Resampling.LANCZOS)
    ink = Image.new('L', tile.size)
    ink.paste(mask, ((tile.width-mask.width)//2, (tile.height-mask.height)//2))
    color = tuple(label.get('glow_color', (255, 128, 0, 255)))
    strength = label.get('glow_strength', 3)
    halo = Image.new('RGBA', tile.size, color[:3] + (0,))
    halo.putalpha(ink.filter(ImageFilter.GaussianBlur(radius)).point(
        lambda value: round(min(255, value * strength) * color[3] / 255)))
    foreground = tuple(label.get('foreground', (255, 255, 255, 255)))
    body = Image.new('RGBA', tile.size, foreground[:3] + (0,))
    body.putalpha(ink.point(lambda value: round(value * foreground[3] / 255)))
    tile.alpha_composite(halo)
    tile.alpha_composite(body)
    return tile


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
                if pixel_format not in ('1828014f', '18280143', '18280186', '28280144', '1a200152', '1a200153', '1a200154'):
                    raise ValueError(f'Unsupported atlas pixel format: {name}')
                raw = data[raw_start:raw_start+raw_size]
                if pixel_format in ('1a200152','1a200153','1a200154'):
                    expected = width * height // 2 if pixel_format == '1a200152' else width * height
                    if raw_size != expected:
                        raise ValueError('Invalid compressed atlas extent')
                    swapped = b''.join(raw[i:i+2][::-1] for i in range(0,len(raw),2))
                    codec = {'1a200152':(1,'DXT1'),'1a200153':(2,'DXT3'),'1a200154':(3,'DXT5')}[pixel_format]
                    image = Image.frombytes('RGBA',(width,height),swapped,'bcn',codec)
                elif pixel_format == '18280186':
                    if raw_size != width * height * 4:
                        raise ValueError('Invalid 32-bit atlas extent')
                    image = Image.frombytes('RGBA', (width, height), raw, 'raw', 'ARGB')
                else:
                    if raw_size != width * height * 2:
                        raise ValueError('Invalid 16-bit atlas extent')
                    rgba = bytearray(width * height * 4)
                    for index, (pixel,) in enumerate(struct.iter_unpack('>H', raw)):
                        if pixel_format == '28280144':
                            value=(((pixel>>11)&31)*255//31,((pixel>>5)&63)*255//63,(pixel&31)*255//31,255)
                        elif pixel_format == '18280143':
                            value=(((pixel>>10)&31)*255//31,((pixel>>5)&31)*255//31,(pixel&31)*255//31,255 if pixel&0x8000 else 0)
                        else:
                            value=(((pixel>>8)&15)*17,((pixel>>4)&15)*17,(pixel&15)*17,((pixel>>12)&15)*17)
                        rgba[index*4:index*4+4] = bytes(value)
                    image = Image.frombytes('RGBA', (width, height), bytes(rgba))
                background_image = image.copy() if any('background_sample_x' in label
                    or 'background_sample_rect' in label or label.get('background_keep_alpha')
                    for label in atlases[name]) else None
                dirty_blocks=set()
                mask_tints = {}
                for label in atlases[name]:
                    x, y, w, h = label['rect']
                    if not 0 <= x < x+w <= width or not 0 <= y < y+h <= height:
                        raise ValueError('Label rectangle outside atlas')
                    if 'photo_caption' in label:
                        options = label['photo_caption']
                        if (pixel_format != '1a200152' or any(key in label for key in (
                                'background_sample_x', 'background_sample_rect', 'text_slice', 'edit_polygon',
                                'alpha_mask_only', 'background_keep_alpha', 'clear_rect'))
                                or hashlib.sha256(raw).hexdigest() != options['source_sha256']):
                            raise ValueError('Photo captions require an unchanged reviewed BC1 source')
                        reference = read_caption_reference(data, options['reference_texture'],
                                                           options['reference_sha256'])
                        original_photo = image.copy()
                        image = restore_photo_caption(image, reference, options, label['rect'])
                    if 'clear_rect' in label:
                        cx,cy,cw,ch = label['clear_rect']
                        if not 0 <= cx < cx+cw <= width or not 0 <= cy < cy+ch <= height:
                            raise ValueError('Clear rectangle outside atlas')
                        image.paste(tuple(label.get('clear_background',(0,0,0,0))), (cx,cy,cx+cw,cy+ch))
                        dirty_blocks.update((bx,by) for by in range(cy//4,(cy+ch+3)//4) for bx in range(cx//4,(cx+cw+3)//4))
                    scale = 4
                    slice_width = w
                    if 'text_slice' in label:
                        slice_offset, strip_width = label['text_slice']
                        if (not isinstance(slice_offset, int) or not isinstance(strip_width, int)
                                or not 0 <= slice_offset < slice_offset+w <= strip_width <= 8192):
                            raise ValueError('Text slice must stay inside its rendered strip')
                        if ('background_sample_x' in label or 'background_sample_rect' in label or any(label.get(key) for key in (
                                'background_keep_alpha', 'text_rotation', 'glow_radius', 'edit_polygon', 'tint_mask'))):
                            raise ValueError('Text slices require an unrotated label on a solid background')
                        # Some native sprites join several atlas strips into one
                        # sentence. Fit the whole sentence before slicing it.
                        w = strip_width
                    tile = Image.new('RGBA', (w*scale, h*scale), tuple(label.get('background',(68,68,68,0))))
                    if 'background_sample_x' in label:
                        sample_x = label['background_sample_x']
                        if not 0 <= sample_x < width:
                            raise ValueError('Background sample column outside atlas')
                        tile = background_image.crop((sample_x,y,sample_x+1,y+h)).resize(
                            (w*scale,h*scale), Image.Resampling.NEAREST)
                        if not label.get('background_sample_alpha'):
                            tile.putalpha(background_image.getchannel('A').crop((x,y,x+w,y+h)).resize(
                                (w*scale,h*scale), Image.Resampling.NEAREST))
                    if 'background_sample_rect' in label:
                        sx, sy, sw, sh = label['background_sample_rect']
                        if ('background_sample_x' in label or not 0 <= sx < sx+sw <= width
                                or not 0 <= sy < sy+sh <= height):
                            raise ValueError('Background sample must be one rectangle inside the atlas')
                        tile = background_image.crop((sx,sy,sx+sw,sy+sh)).resize(
                            (w*scale,h*scale), Image.Resampling.NEAREST)
                        if not label.get('background_sample_alpha'):
                            tile.putalpha(background_image.getchannel('A').crop((x,y,x+w,y+h)).resize(
                                (w*scale,h*scale), Image.Resampling.NEAREST))
                    if label.get('background_keep_alpha'):
                        tile.putalpha(background_image.getchannel('A').crop((x,y,x+w,y+h)).resize(
                            (w*scale,h*scale), Image.Resampling.NEAREST))
                    if label.get('glow_radius'):
                        tile = draw_glowing_label(tile, label, font_path, scale)
                    elif label.get('text_rotation'):
                        tile = draw_rotated_label(tile, label, font_path, scale)
                    else:
                        draw = ImageDraw.Draw(tile)
                        alignment = label.get('align', 'left')
                        text_options = ({'spacing': label['line_spacing'] * scale}
                                        if 'line_spacing' in label else {})
                        stroke = label.get('outline_width', 0) * scale
                        for size in range(label.get('max_font_size', 38), label.get('min_font_size', 13)-1, -1):
                            font = ImageFont.truetype(str(font_path), size*scale)
                            box = draw.textbbox((0,0), label['text'], font=font,
                                align=alignment, stroke_width=stroke, **text_options)
                            width_limit = (w-label.get('padding',12))*scale
                            if label.get('condense'):
                                width_limit /= label.get('min_width_ratio',0.55)
                            if box[2]-box[0] <= width_limit and box[3]-box[1] <= (h-label.get('vertical_padding',3))*scale:
                                break
                        else:
                            raise ValueError(f"English label does not fit {name} {label['rect']}: {label['text']}")
                        x_text = (w*scale - (box[2]-box[0]))/2 - box[0]
                        y_text = (h*scale - (box[3]-box[1]))/2 - box[1]
                        if label.get('condense') and label['text']:
                            glyph = Image.new('RGBA',(math.ceil(box[2]-box[0]),math.ceil(box[3]-box[1])))
                            ImageDraw.Draw(glyph).text((-box[0],-box[1]),label['text'],font=font,
                                align=alignment,fill=tuple(label.get('foreground',(255,255,255,255))),
                                stroke_width=stroke,stroke_fill=tuple(label.get('outline',(0,0,0,255))),
                                **text_options)
                            glyph_width = min(glyph.width,(w-label.get('padding',12))*scale)
                            if glyph_width != glyph.width:
                                glyph = glyph.resize((glyph_width,glyph.height),Image.Resampling.LANCZOS)
                            tile.alpha_composite(glyph,((w*scale-glyph.width)//2,(h*scale-glyph.height)//2))
                        else:
                            draw.text((x_text, y_text), label['text'], font=font,
                                align=alignment,
                                fill=tuple(label.get('foreground',(255,255,255,255))),
                                stroke_width=stroke,
                                stroke_fill=tuple(label.get('outline',(0,0,0,255))), **text_options)
                    tile = tile.resize((w,h), Image.Resampling.LANCZOS)
                    if 'photo_caption' in label:
                        photo_tile = image.crop((x,y,x+w,y+h))
                        photo_tile.alpha_composite(tile)
                        tile = photo_tile
                    if 'text_slice' in label:
                        tile = tile.crop((slice_offset, 0, slice_offset+slice_width, h))
                        w = slice_width
                    if 'transparent_rgb' in label:
                        color = label['transparent_rgb']
                        if len(color) != 3 or any(not isinstance(c, int) or not 0 <= c <= 255 for c in color):
                            raise ValueError('Transparent RGB must contain three byte values')
                        # DDS color fitting can include invisible black pixels in
                        # a block palette. Keep their RGB near the outline tint.
                        hidden = Image.new('RGBA', tile.size, tuple(color) + (0,))
                        hidden.paste(tile, (0,0), tile.getchannel('A').point(lambda a: 255 if a else 0))
                        tile = hidden
                    if label.get('alpha_mask_only'):
                        # Some newspaper sprites carry text only in alpha; RGB is a fixed tint.
                        original = image.crop((x,y,x+w,y+h))
                        original.putalpha(tile.getchannel('A'))
                        tile = original
                    if pixel_format == '28280144' and tile.getchannel('A').getextrema() != (255, 255):
                        raise ValueError('RGB565 labels require an opaque background or sample column')
                    if 'edit_polygon' in label:
                        polygon = label['edit_polygon']
                        if len(polygon) < 3 or any(not 0 <= px <= w or not 0 <= py <= h for px, py in polygon):
                            raise ValueError('Edit polygon must stay inside its label rectangle')
                        mask = Image.new('L', (w*scale, h*scale))
                        ImageDraw.Draw(mask).polygon([(px*scale, py*scale) for px, py in polygon], fill=255)
                        mask = mask.resize((w,h), Image.Resampling.LANCZOS)
                        image.paste(tile, (x,y), mask)
                    else:
                        image.paste(tile, (x,y))
                    label_blocks = {(bx,by) for by in range(y//4,(y+h+3)//4) for bx in range(x//4,(x+w+3)//4)}
                    if 'photo_caption' in label:
                        label_blocks = {block for block in label_blocks
                            if original_photo.crop((block[0]*4,block[1]*4,block[0]*4+4,block[1]*4+4)).tobytes()
                            != image.crop((block[0]*4,block[1]*4,block[0]*4+4,block[1]*4+4)).tobytes()}
                    dirty_blocks.update(label_blocks)
                    if label.get('tint_mask'):
                        if (pixel_format != '1a200152' or any(n%4 for n in (x,y,w,h))
                                or 'background_sample_x' in label or label.get('background',(0,0,0,0))[3]
                                or tuple(label.get('outline',(0,0,0,255))[:3]) != (0,0,0)):
                            raise ValueError('Tinted masks require block-aligned BC1 glyphs on a transparent background')
                        for block in label_blocks:
                            if block in mask_tints:
                                raise ValueError('Overlapping tinted masks')
                            mask_tints[block] = label['foreground'][:3]
                encoded = bytearray(raw)
                colored_blocks = ({block for block in dirty_blocks if block not in mask_tints
                    and block_has_color(image,*block)} if pixel_format in ('1a200152','1a200153','1a200154') else set())
                # Opt in for atlases that mix colored badges and grayscale text.
                if (colored_blocks and not any(label.get('split_color_blocks') for label in atlases[name])) or (
                        pixel_format in ('1a200152','1a200153','1a200154')
                        and any(label.get('adaptive_palette') for label in atlases[name])):
                    # Opaque shaded panels need per-block palettes to retain their gradients.
                    colored_blocks = dirty_blocks-mask_tints.keys()
                if colored_blocks:
                    stream = io.BytesIO()
                    image.save(stream, format='DDS', pixel_format=codec[1])
                    dds = stream.getvalue()
                    if (dds[:4] != b'DDS ' or len(dds) != 128 + raw_size
                            or struct.unpack_from('<II',dds,12) != (height,width)
                            or dds[84:88] != codec[1].encode('ascii')):
                        raise ValueError('Unexpected compressed DDS output')
                    blocks = dds[128:]
                    block_size = 8 if pixel_format == '1a200152' else 16
                    # Copy only edited blocks, preserving every other original byte.
                    for bx,by in colored_blocks:
                        start = (by*(width//4)+bx)*block_size
                        block = blocks[start:start+block_size]
                        encoded[start:start+block_size] = b''.join(
                            block[i:i+2][::-1] for i in range(0,block_size,2))
                if pixel_format == '1a200152':
                    # Position glyphs are white masks tinted by the game. Keep
                    # every untouched compressed block byte-identical.
                    for bx,by in dirty_blocks-colored_blocks:
                        tint = mask_tints.get((bx,by))
                        endpoint = 0xFFFF
                        if tint:
                            red,green,blue = tint
                            endpoint = ((red>>3)<<11) | ((green>>2)<<5) | (blue>>3)
                            quantized = ((red&248)|(red>>5),(green&252)|(green>>6),(blue&248)|(blue>>5))
                            palette = ((0,0,0),quantized,tuple(c//2 for c in quantized))
                        indices=0
                        for py in range(4):
                            for px in range(4):
                                red,green,blue,alpha=image.getpixel((bx*4+px,by*4+py))
                                if tint:
                                    index = (3 if alpha<128 else min(range(3),key=lambda i:
                                        sum((a-b)**2 for a,b in zip((red,green,blue),palette[i]))))
                                else:
                                    if alpha>=128 and max(red,green,blue)-min(red,green,blue)>8:
                                        raise ValueError('BC1 mask encoder supports grayscale glyphs only')
                                    index=3 if alpha<128 else (1 if red>=192 else 2 if red>=64 else 0)
                                indices |= index << (2*(py*4+px))
                        block=struct.pack('<HHI',0,endpoint,indices)
                        block=b''.join(block[i:i+2][::-1] for i in range(0,8,2))
                        start=(by*(width//4)+bx)*8
                        encoded[start:start+8]=block
                elif pixel_format in ('1a200153','1a200154'):
                    # Restrict edits to grayscale labels; retain every other block.
                    colors = (255,0,170,85)
                    alphas = (255,0,218,182,145,109,72,36)
                    for bx,by in dirty_blocks-colored_blocks:
                        color_bits = alpha_bits = 0
                        for py in range(4):
                            for px in range(4):
                                red,green,blue,alpha = image.getpixel((bx*4+px,by*4+py))
                                if alpha>=128 and max(red,green,blue)-min(red,green,blue)>8:
                                    raise ValueError('Compressed mask encoder supports grayscale glyphs only')
                                pixel = py*4+px
                                color_bits |= min(range(4),key=lambda i:abs(colors[i]-red)) << (2*pixel)
                                if pixel_format == '1a200153':
                                    alpha_bits |= min(15,(alpha+8)//17) << (4*pixel)
                                else:
                                    alpha_bits |= min(range(8),key=lambda i:abs(alphas[i]-alpha)) << (3*pixel)
                        alpha_block = (alpha_bits.to_bytes(8,'little') if pixel_format == '1a200153'
                            else bytes((255,0))+alpha_bits.to_bytes(6,'little'))
                        block = alpha_block + struct.pack('<HHI',0xFFFF,0,color_bits)
                        block = b''.join(block[i:i+2][::-1] for i in range(0,16,2))
                        start = (by*(width//4)+bx)*16
                        encoded[start:start+16] = block
                elif pixel_format == '18280186':
                    rgba = image.tobytes()
                    for source_channel, target_channel in ((3,0),(0,1),(1,2),(2,3)):
                        encoded[target_channel::4] = rgba[source_channel::4]
                else:
                    for index, (red,green,blue,alpha) in enumerate(image.getdata()):
                        if pixel_format == '28280144':
                            pixel = ((red>>3)<<11) | ((green>>2)<<5) | (blue>>3)
                        elif pixel_format == '18280143':
                            pixel = ((1 if alpha>=128 else 0)<<15) | ((red>>3)<<10) | ((green>>3)<<5) | (blue>>3)
                        else:
                            pixel = ((alpha>>4)<<12) | ((red>>4)<<8) | ((green>>4)<<4) | (blue>>4)
                        struct.pack_into('>H', encoded, index*2, pixel)
                patched[raw_start:raw_start+raw_size] = encoded
                preview.mkdir(parents=True, exist_ok=True)
                preview_image = image
                if pixel_format in ('1a200152','1a200153','1a200154'):
                    swapped = b''.join(encoded[i:i+2][::-1] for i in range(0,len(encoded),2))
                    preview_image = Image.frombytes('RGBA',(width,height),swapped,'bcn',codec)
                preview_image.save(preview / (name + '.english.png'))
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
    parser.add_argument('--pennant-text', type=Path, help='Reviewed Pennant event fields')
    parser.add_argument('--packed-text', type=Path, help='Reviewed TXCPACK text slots')
    parser.add_argument('--font', type=Path, default=Path('C:/Windows/Fonts/ARIALNB.TTF'))
    parser.add_argument('--preview', required=True, type=Path)
    args = parser.parse_args()
    source, output = args.game_root.resolve(), args.output.resolve()
    if source == output or source in output.parents or output in source.parents:
        parser.error('Source and output must be separate, non-nested directories')
    archive = source / 'cdvdroot/baseball.fbd'
    entries = read_index(archive)
    labels = json.loads(args.labels.read_text(encoding='utf-8'))
    packed = load_packed_text(args.packed_text)
    members = labels.keys() | packed.keys()
    pennant = load_translations(args.pennant_events, args.pennant_text)
    if pennant:
        if PENNANT_MEMBER in members:
            parser.error(f'{PENNANT_MEMBER} is reserved for event text')
        members.add(PENNANT_MEMBER)
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
            if data.startswith(b'CMP\0'):
                data = cmp.decompress(data)
            if name in labels:
                data = patch_chk(data, labels[name], args.font, args.preview)
            if name in packed:
                data = patch_packed_text(data, packed[name])
            if name == PENNANT_MEMBER and pennant:
                data = patch_text(data, pennant)
            patches[name] = data
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
