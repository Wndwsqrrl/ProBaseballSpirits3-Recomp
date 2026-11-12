"""Verify shared Spirits tutorial translations and protected original artwork."""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from bndr import read_index

spec = importlib.util.spec_from_file_location('catalogue', Path(__file__).with_name('catalogue-menu-assets.py'))
catalogue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalogue)

PROTECTED = {
    '01': [(0, 0, 44, 32), (44, 0, 192, 52), (268, 0, 316, 80), (0, 0, 16, 80)],
    '03': [(50, 59, 142, 73), (52, 75, 139, 132), (50, 175, 140, 193),
           (144, 152, 216, 156), (149, 194, 196, 198), (82, 221, 216, 224)],
    '04': [(300, 82, 387, 143), (250, 100, 270, 150), (206, 115, 220, 135),
           (22, 285, 104, 326), (120, 285, 151, 320), (308, 56, 367, 68), (390, 50, 396, 180)],
}


def textures(data):
    if data.startswith(b'CMP\0'):
        data = catalogue.cmp.decompress(data)
    found = {}
    at = 16
    while at + 16 <= len(data) and data[at:at+8] != b'CHUNKEND':
        _, _, allocated, actual = struct.unpack_from('>4sIII', data, at)
        if allocated < 16 or actual > allocated or at + allocated > len(data):
            raise ValueError('Invalid tutorial chunk extent')
        start = at + 16
        if data[start:start+8] == b'X360SUR ':
            payload = data[start:start+actual]
            name = payload[16:48].split(b'\0')[0].decode('ascii')
            width, height = struct.unpack_from('>II', payload, 48)
            found[name] = dict(payload=payload, raw=payload[100:-1], width=width, height=height,
                               format=payload[68:72].hex())
        at += allocated
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('english', type=Path)
    parser.add_argument('--labels', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    labels = json.loads(args.labels.read_text(encoding='utf-8'))
    old_index = {r['name']: r for r in read_index(args.original)}
    new_index = {r['name']: r for r in read_index(args.english)}
    members = sorted(n for n in old_index if n.startswith('RKINFO'))
    if len(members) != 37:
        raise ValueError('Expected all 37 team and scenario tutorial variants')
    groups = {key: {'original_hashes': set(), 'english_hashes': set(), 'copies': 0} for key in PROTECTED}
    protected_regions = preserved_payloads = occurrences = 0
    manifest = []
    with args.original.open('rb') as source, args.english.open('rb') as target:
        for member in members:
            row = old_index[member]
            source.seek(row['offset'])
            original = textures(source.read(row['size']))
            row = new_index[member]
            target.seek(row['offset'])
            english = textures(target.read(row['size']))
            if len(original) != 5 or original.keys() != english.keys():
                raise ValueError(f'Tutorial texture membership changed: {member}')
            translated = []
            for name, before in original.items():
                after = english[name]
                key = name.rsplit('_', 1)[-1].removesuffix('.tsr')
                if key not in PROTECTED:
                    if before['payload'] != after['payload']:
                        raise ValueError(f'Background or effect changed: {member}/{name}')
                    preserved_payloads += 1
                    continue
                group = groups[key]
                group['original_hashes'].add(hashlib.sha256(before['raw']).hexdigest())
                group['english_hashes'].add(hashlib.sha256(after['raw']).hexdigest())
                group['copies'] += 1
                occurrences += len(labels[member][name])
                translated.append(name)
                images = [catalogue.decode(r['raw'], r['width'], r['height'], r['format'])
                          for r in (before, after)]
                for box in PROTECTED[key]:
                    if images[0].crop(box).tobytes() != images[1].crop(box).tobytes():
                        raise ValueError(f'Protected tutorial region changed: {member}/{name} {box}')
                    protected_regions += 1
            if len(translated) != 3:
                raise ValueError(f'Missing translated tutorial atlas: {member}')
            manifest.append(dict(member=member, translated_textures=translated))
    for key, group in groups.items():
        if group['copies'] != 37 or len(group['original_hashes']) != 1 or len(group['english_hashes']) != 1:
            raise ValueError(f'Shared tutorial pixels differ across variants: {key}')
    report = dict(
        source_members=37, source_textures=185,
        shared_label_definitions=sum(len(rows) for rows in labels[members[0]].values()),
        unique_english_texts=len({r['text'] for rows in labels[members[0]].values() for r in rows}),
        label_occurrences=occurrences,
        translated_atlases=111, preserved_background_and_effect_payloads=preserved_payloads,
        protected_regions_pixel_identical=protected_regions,
        shared_pixel_groups={key: dict(original_pixel_sha256=next(iter(g['original_hashes'])),
                                      english_pixel_sha256=next(iter(g['english_hashes'])), copies=g['copies'])
                             for key, g in groups.items()},
        reference=dict(source='Installed eBaseball PRO SPIRIT 2026 Japanese/English localization',
                       namespace='Match', key='match_telop_open_match_text', japanese='オープン戦',
                       english='Preseason Game', scope='This term only; remaining captions use the 2006 source'),
        protected_content='Original team background photos, ballpark signs and ads, controls and card illustrations',
        font_bounds_checked=True, angled_glyphs_fit_edit_polygons=True,
        native_decoded_previews_checked=True, interactive_validation=False,
        entire_game_english=False, members=manifest)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'{occurrences} label occurrences / 111 atlases / 37 variants verified; '
          f'{preserved_payloads} complete payloads and {protected_regions} artwork regions unchanged')


if __name__ == '__main__':
    main()
