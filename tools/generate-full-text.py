"""Generate relocation/hook tables, without embedding the original Japanese corpus."""
import argparse
import json
import re
from pathlib import Path


def fnv64(data):
    value = 0xCBF29CE484222325
    for byte in data:
        value = ((value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('header', type=Path)
    parser.add_argument('--catalogue', type=Path, help='Export English plus source addresses/hashes only')
    parser.add_argument('--image', type=Path)
    parser.add_argument('--extra-catalogue',type=Path,action='append',default=[])
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding='utf-8'))
    for extra in args.extra_catalogue:
        source.extend(json.loads(extra.read_text(encoding='utf-8')))
    image = args.image.read_bytes() if args.image else None
    rows, hashes = [], {}
    priorities = {}
    fragments = {}
    for item in source:
        if item.get('english') is None:
            continue
        address = int(item['address'], 0)
        if 'source' in item:
            original = item['source'].encode('cp932')
            if image is not None and address:
                offset = address - 0x82000000
                terminator = image.find(b'\0', offset, offset+8193)
                if terminator < 0:
                    raise ValueError('Source string has no terminator')
                raw = image[offset:terminator]
                # CP932 has duplicate byte encodings for some characters;
                # fingerprint the actual bytes rather than re-encoding them.
                if raw.decode('cp932') != item['source']:
                    raise ValueError(f'Decoded source differs at {address:#x}')
                original = raw
            size, fingerprint = len(original), fnv64(original)
        else:
            size, fingerprint = item['source_size'], int(item['source_hash'], 16)
        encoded = item['english'].encode('cp932')
        if b'\0' in encoded or len(encoded) > 8192:
            raise ValueError('Invalid translated string')
        if address and not any(lo<=address<address+size+1<=hi for lo,hi in ((0x82000400,0x820AB20C),(0x826E0000,0x82C10AD8))):
            raise ValueError('Source string outside supported image')
        if image is not None and address:
            offset = address - 0x82000000
            if image[offset+size] != 0 or fnv64(image[offset:offset+size]) != fingerprint:
                raise ValueError(f'Source fingerprint differs at {address:#x}')
        priority=3 if item.get('status')=='reviewed' else 2 if item.get('status')=='game-roster-family' else 1
        if fingerprint in hashes and hashes[fingerprint] != item['english']:
            if priority==priorities[fingerprint]:
                raise ValueError('Conflicting translations for one source string')
            if priority<priorities[fingerprint]:
                item=dict(item,english=hashes[fingerprint])
            else:
                for row in rows:
                    if int(row['source_hash'],16)==fingerprint:
                        row['english']=item['english'];row['status']=item.get('status','draft')
        hashes[fingerprint] = item['english']
        priorities[fingerprint]=max(priority,priorities.get(fingerprint,0))
        rows.append(dict(address=f'0x{address:08X}', source_size=size,
                         source_hash=f'{fingerprint:016X}', english=item['english'],
                         status=item.get('status', 'reviewed')))
        # A few runtime-only patterns have no address in the static image.
        # Keep their short source pattern so the renderer can match filled slots.
        pattern=item.get('format_source',item.get('source','') if not address else '')
        if pattern and re.search(r'%[-+ #0\d.]*[diuoxXfFeEgGs]',pattern):
            rows[-1]['format_source']=pattern
        # The markup parser passes individual prose runs to the font renderer.
        # Add content-only lookups for those runs without relocating address 0.
        if 'source' in item:
            tag = r'<[^>]*>|\\(?:c[0-9a-fA-F]|C[0-9a-fA-F]{6})'
            if re.findall(tag,item['source']) == re.findall(tag,item['english']):
                originals=re.split(tag,item['source'])
                english=re.split(tag,item['english'])
                for original, translated in zip(originals,english):
                    original,translated=original.strip(),translated.strip()
                    if original and translated and any(ord(c)>127 for c in original):
                        fragments.setdefault(fnv64(original.encode('cp932')),
                            (original,translated,item.get('status','draft')))
    for fingerprint,(original,english,status) in fragments.items():
        if fingerprint in hashes:
            continue
        hashes[fingerprint]=english
        rows.append(dict(address='0x00000000',source_size=len(original.encode('cp932')),
                         source_hash=f'{fingerprint:016X}',english=english,status=status))
    lines = ['// Generated translation table. Original Japanese strings are not embedded.', '#pragma once',
             '#include <cstdint>', '#include <string_view>',
             'struct FullTranslationRecord { uint32_t address; uint32_t source_size; uint64_t fingerprint; std::string_view english; std::string_view format_source; };',
             'inline constexpr FullTranslationRecord kFullTranslations[] = {']
    for row in rows:
        escaped = ''.join(f'\\x{byte:02x}' for byte in row['english'].encode('cp932'))
        pattern=''.join(f'\\x{byte:02x}' for byte in row.get('format_source','').encode('cp932'))
        lines.append(f'    {{{row["address"]}, {row["source_size"]}, 0x{row["source_hash"]}ULL, "{escaped}", "{pattern}"}},')
    lines.append('};\n')
    args.header.parent.mkdir(parents=True, exist_ok=True)
    output = '\n'.join(lines)
    if not args.header.exists() or args.header.read_text(encoding='utf-8') != output:
        args.header.write_text(output, encoding='utf-8')
    if args.catalogue:
        args.catalogue.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Generated {len(rows)} translations, {len(hashes)} unique fingerprints.')


if __name__ == '__main__':
    main()
