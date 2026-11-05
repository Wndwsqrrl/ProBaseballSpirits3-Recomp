"""Build bounded runtime aliases for the newspaper's name and number fields."""
import argparse
import json
import re
from pathlib import Path

FIELDS = re.compile(r'△{2,}|▲{2,}|＃{2,}|■{2,}|□{2,}|☆{2,}|＠{2,}|｜{2,}')


def pattern(text):
    return FIELDS.sub(lambda m: '%d' if m[0][0] in '☆＠｜' else '%s', text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = {}
    for row in json.loads(args.input.read_text(encoding='utf-8')):
        address = int(row['address'], 0)
        if not 0x827E8708 <= address < 0x827EB885:
            continue
        source, english = row['source'], row['english']
        if not FIELDS.search(source):
            continue
        if FIELDS.findall(source) != FIELDS.findall(english):
            raise ValueError(f'Newspaper fields changed at {address:#x}')
        source, english = pattern(source), pattern(english)
        # Match only distinctive prose, never a bare player/team name.
        if len(re.findall(r'[\u3041-\u30fa\u3400-\u9fff]', source)) < 2:
            continue
        for text in (source, source.rstrip(' \u3000')):
            if text in result and result[text]['english'] != english:
                raise ValueError('Conflicting newspaper alias')
            result[text] = dict(address='0x00000000', source=text,
                                english=english, status=row['status'])
    args.output.write_text(json.dumps(list(result.values()), ensure_ascii=False,
                                      indent=2)+'\n', encoding='utf-8')
    print(f'{len(result)} newspaper runtime aliases generated.')


if __name__ == '__main__':
    main()
