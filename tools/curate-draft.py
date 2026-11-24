"""Apply reviewed corrections and exclude character/numeric tables from the draft."""
import argparse
import json
import re
from pathlib import Path

TAG = re.compile(r'<[^>]*>|\\(?:c[0-9a-fA-F]|C[0-9a-fA-F]{6})|\x0b')
FORMAT = re.compile(r'%(?:\d+\$)?[-+# 0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[hlL]*[diuoxXfFeEgGcsSpn%]')
JAPANESE = re.compile(r'[\u3041-\u30fa\u3400-\u9fff]')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('curation', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    rows = json.loads(args.input.read_text(encoding='utf-8'))
    config = json.loads(args.curation.read_text(encoding='utf-8'))
    normalize=lambda text:re.sub('[ \u3000]+','',text)
    words={normalize(k):v for k,v in config.get('word_overrides',{}).items()}
    addresses={r['address'].lower() for r in rows}
    rows.extend(r for r in config.get('additional_strings',[]) if r['address'].lower() not in addresses)
    result, excluded, residual = [], [], []
    for row in rows:
        if row['address'] in config.get('source_corrections', {}):
            row.update(config['source_corrections'][row['address']])
            row['status'] = 'reviewed'
        address = int(row['address'], 0)
        if row['address'] in config['exclude_addresses'] or any(int(r['start'],0)<=address<int(r['end'],0) for r in config['exclude_ranges']):
            excluded.append(row['address'])
            continue
        address_review=row['address'] in config['overrides']
        address_provisional=not address_review and row['address'] in config.get('provisional_overrides', {})
        source_provisional=not address_review and row['source'] in config.get('provisional_word_overrides', {})
        provisional=address_provisional or source_provisional
        if provisional:
            row['english'] = (config['provisional_overrides'][row['address']] if address_provisional
                              else config['provisional_word_overrides'][row['source']])
            row['status'] = 'draft'
        if address_review:
            row['english'] = config['overrides'][row['address']]
            row['status'] = 'reviewed'
        if not address_review and not provisional and normalize(row['source']) in words:
            row['english'] = words[normalize(row['source'])]
            row['status'] = 'reviewed'
        parts = re.split(r'(<[^>]*>)', row['english'])
        source_parts = re.split(r'(<[^>]*>)', row['source'])
        for i in range(0,len(parts),2):
            if not address_review and not provisional and len(parts)==len(source_parts) and normalize(source_parts[i]) in words:
                parts[i]=words[normalize(source_parts[i])]
                if source_parts[i].endswith(' '):parts[i]+=' '
            parts[i] = parts[i].replace('・','-').replace('【','[').replace('】',']')
            parts[i] = re.sub(r'(?<=\d)%(?![\dA-Za-z])', ' percent', parts[i])
            parts[i] = re.sub('Master Pennant', 'Manager Pennant', parts[i], flags=re.I)
            parts[i] = re.sub('home run competition', 'Home Run Derby', parts[i], flags=re.I)
        row['english'] = ''.join(parts)
        source_tags=TAG.findall(row['source']);english_tags=TAG.findall(row['english'])
        if row.get('status')=='reviewed':
            # Reviewed English may reflow line breaks. Button/color/layout
            # controls still retain their exact order and count.
            source_tags=[t for t in source_tags if t.upper() not in ('<BR>','<BR/>','<BR />')]
            english_tags=[t for t in english_tags if t.upper() not in ('<BR>','<BR/>','<BR />')]
        if source_tags != english_tags:
            # Token order can carry color/alignment state, so order matters.
            raise ValueError(f'Control markup changed at {row["address"]}')
        if FORMAT.findall(row['source']) != FORMAT.findall(row['english']):
            raise ValueError(f'Printf substitutions changed at {row["address"]}')
        if JAPANESE.search(TAG.sub('',row['english'])):
            residual.append(row['address'])
        result.append(row)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{len(result)} display-text candidates; {len(excluded)} data/codebook candidates excluded; {len(residual)} rows still contain Japanese prose.')
    if residual:
        print('Residual addresses:', ', '.join(residual))


if __name__ == '__main__':
    main()
