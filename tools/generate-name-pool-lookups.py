"""Build complete player-name lookups, retaining provisional reading status."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct

BASE = 0x82000000
TABLE = 0x82041110
COUNT = 413
TABLE_SHA256 = 'ec7a6b9ab3740da6d32d023d5bba76905db280114c929d11996ad34efcee5d16'

def fingerprint(data):
    value = 0xCBF29CE484222325
    for byte in data:
        value = ((value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f'{value:016X}'

def generate(image, reviews, existing, context):
    table = image[TABLE-BASE:TABLE-BASE+COUNT*20]
    if hashlib.sha256(table).hexdigest() != TABLE_SHA256:
        raise ValueError('Unsupported native name-pool table')
    def read(address):
        if not BASE+0x400 <= address < BASE+0xAB20C:
            raise ValueError('Name pointer outside native read-only data')
        start = address-BASE
        end = image.find(b'\0', start, start+128)
        if end < start:
            raise ValueError('Unterminated native name')
        return image[start:end]

    reviewed = {}
    for row in existing:
        if row['address'] != '0x00000000':
            reviewed[row['address']] = row
    known = defaultdict(set)
    for row in existing:
        known[row['source_hash']].add(row['english'])
    proposals = defaultdict(dict)
    resolved = []
    unresolved = []
    used_context = set()
    for n in range(COUNT):
        address = TABLE+n*20
        family, given, latin, ident, country = struct.unpack_from('>5I', table, n*20)
        if ident >> 24 != 1 or country > 4:
            raise ValueError('Invalid native name-pool record')
        original = {'family':read(family), 'given':read(given)}
        values = {}
        statuses = {}
        for role, pointer in [('family',family),('given',given)]:
            key = f'0x{pointer:08X}'
            row = reviewed.get(key)
            if key in reviews and row and row['status']=='reviewed' and row['english']==reviews[key]:
                values[role] = row['english']
                statuses[role] = 'reviewed'
            for override in context:
                if override['record_address'] != f'0x{address:08X}' or override['field'] != role:
                    continue
                if (override['record_id'] != f'{ident:08X}'
                        or override['source_hash'] != fingerprint(original[role])):
                    raise ValueError('Contextual name override differs from the native record')
                values[role] = override['english']
                statuses[role] = override.get('status', 'reviewed')
                if statuses[role] not in ('reviewed', 'draft'):
                    raise ValueError('Name context status must be reviewed or draft')
                used_context.add((override['record_address'],role))
        if len(values)!=2:
            unresolved.append(f'0x{address:08X}')
            continue
        english = values['family']+' '+values['given']
        if not english.isascii() or not all(values.values()):
            raise ValueError('Expected complete English name fields')
        status = 'draft' if 'draft' in statuses.values() else 'reviewed'
        resolved.append(dict(record_address=f'0x{address:08X}',english=english,status=status))
        family_forms = {original['family'],values['family'].encode('ascii')}
        for family_form in family_forms:
            for separator in [b'',b' ',b'\x81\x40']:
                for source in [family_form+separator+original['given'],
                               original['given']+separator+family_form]:
                    previous = proposals[source].get(english)
                    proposals[source][english] = 'reviewed' if previous=='reviewed' or status=='reviewed' else 'draft'
    if len(used_context)!=len(context):
        raise ValueError('Unused contextual name override')
    output=[];fixtures=[];conflicts=[];covered=0
    for source, choices in sorted(proposals.items()):
        key = fingerprint(source)
        if len(choices)!=1:
            conflicts.append(key)
            continue
        english=next(iter(choices))
        status=choices[english]
        if key in known:
            if known[key] == {english}:covered+=1
            else:
                conflicts.append(key)
                continue
        output.append(dict(address='0x00000000',source_size=len(source),source_hash=key,
                           english=english,status=status))
        fixtures.append((source,english))
    provisional=sum(r['status']=='draft' for r in resolved)
    report=dict(native_name_records=COUNT,complete_reviewed_name_pairs=len(resolved)-provisional,
                complete_name_pairs_mapped=len(resolved),provisional_name_pairs=provisional,
                unmapped_name_pair_records=len(unresolved),
                unresolved_name_pair_records=len(unresolved)+provisional,complete_name_aliases=len(output),
                already_covered_aliases=covered,conflicting_aliases_not_added=len(conflicts),
                table_sha256=TABLE_SHA256,resolved_records=resolved,unresolved_records=unresolved,
                contextual_fields=len(context),no_given_name_fields_omitted=True)
    return output,fixtures,report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--reviews',required=True,type=Path)
    p.add_argument('--existing',required=True,type=Path)
    p.add_argument('--context',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    p.add_argument('--fixtures',type=Path)
    a=p.parse_args()
    load=lambda path:json.loads(path.read_text(encoding='utf-8'))
    rows,fixtures,report=generate(a.image.read_bytes(),load(a.reviews),load(a.existing),load(a.context))
    a.output.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if a.fixtures:
        a.fixtures.write_text(''.join(f'0\t{source.hex()}\t{english}\n' for source,english in fixtures),encoding='utf-8')
    print(f'{len(rows)} complete-name aliases: {report["complete_reviewed_name_pairs"]} reviewed and '
          f'{report["provisional_name_pairs"]} provisional pairs; '
          f'{report["unmapped_name_pair_records"]} pairs still unmapped')

if __name__=='__main__':main()
