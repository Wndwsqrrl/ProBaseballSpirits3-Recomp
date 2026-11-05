"""Create a cached translation draft of the extracted game strings.

Only the Japanese game text is sent to Google Translate's public endpoint.
Control markup and printf substitutions are replaced with protected tokens.
The output remains a draft until reviewed and checked in the game.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN = re.compile(r'<[^>]*>|\\(?:c[0-9a-fA-F]|C[0-9a-fA-F]{6}|[nrt])|%(?:\d+\$)?[-+# 0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[hlL]*[diuoxXfFeEgGcsSpn%]|[\r\n\t]')
JAPANESE = re.compile(r'[\u3041-\u3096\u30a1-\u30fa\u3400-\u9fff]')


def protect(text):
    saved = []
    def replace(match):
        saved.append(match.group())
        return f'ZXQTP{len(saved)-1:04d}ZXQ'
    return TOKEN.sub(replace, text), saved


def restore(text, saved):
    # Sanitize literal brackets before restoring the actual control tags.
    text = re.sub(r'<[^>]*>', lambda m: '('+m.group()[1:-1]+')', text)
    for index, value in enumerate(saved):
        marker = f'ZXQTP{index:04d}ZXQ'
        if text.count(marker) != 1:
            raise ValueError(f'Translator altered protected token {marker}')
        text = text.replace(marker, value)
    # Literal Japanese angle brackets sometimes become English ASCII brackets.
    # Only actual source control tags may remain angle-bracketed.
    # Keep typography representable by the game's original CP932 renderer.
    text = text.translate(str.maketrans({'’': "'", '‘': "'", '“': '"', '”': '"', '–': '-', '—': '-', '…': '...'}))
    try:
        text.encode('cp932')
    except UnicodeEncodeError:
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text.strip()


def translate_batch(batch, cache):
    payload, protected = [], {}
    for index, text in batch:
        body, saved = protect(text)
        body = re.sub('\u3000+', ' ', body)
        protected[index] = saved
        payload.append(f'ZXQROW{index:05d}ZXQ\n{body}')
    query = urllib.parse.urlencode({'client': 'gtx', 'sl': 'ja', 'tl': 'en', 'dt': 't', 'q': '\n'.join(payload)})
    url = 'https://translate.googleapis.com/translate_a/single?' + query
    last_error = None
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'ProSpi3-Translation-Research/0.1'})
            with urllib.request.urlopen(request, timeout=35) as response:
                data = json.load(response)
            translated = ''.join(segment[0] or '' for segment in data[0])
            matches = list(re.finditer(r'ZXQROW(\d{5})ZXQ', translated))
            if [int(m[1]) for m in matches] != [index for index, _ in batch]:
                raise ValueError('Translator altered row boundaries')
            result = {}
            for item, match in enumerate(matches):
                index = int(match[1])
                end = matches[item+1].start() if item+1 < len(matches) else len(translated)
                value = restore(translated[match.end():end].strip(), protected[index])
                if not value:
                    raise ValueError('Empty translation')
                result[index] = value
            for index, source in batch:
                key = hashlib.sha256(source.encode('utf-8')).hexdigest()
                (cache / (key + '.json')).write_text(json.dumps({'source': source, 'english': result[index]}, ensure_ascii=False), encoding='utf-8')
            return result
        except ValueError as error:
            last_error = error
            break
        except Exception as error:
            last_error = error
            time.sleep(min(2 ** attempt, 12))
    # Some markup-heavy lines cause the service to combine or omit tokens.
    # Translate only their prose fragments and reassemble the original markup.
    result = {}
    for index, source in batch:
        parts, cursor = [], 0
        for match in TOKEN.finditer(source):
            parts.extend([source[cursor:match.start()], match.group()])
            cursor = match.end()
        parts.append(source[cursor:])
        for part_index in range(0, len(parts), 2):
            prose = parts[part_index]
            if not JAPANESE.search(prose):
                continue
            fragment_path = cache / (hashlib.sha256(prose.encode('utf-8')).hexdigest() + '.json')
            if fragment_path.exists():
                cached = json.loads(fragment_path.read_text(encoding='utf-8'))['english']
                if not JAPANESE.search(TOKEN.sub('',cached)):
                    parts[part_index] = cached
                    continue
            query = urllib.parse.urlencode({'client':'gtx','sl':'ja','tl':'en','dt':'t','q':re.sub('\u3000+', ' ', prose).strip()})
            for attempt in range(5):
                try:
                    with urllib.request.urlopen('https://translate.googleapis.com/translate_a/single?'+query, timeout=35) as response:
                        data = json.load(response)
                    english = restore(''.join(piece[0] or '' for piece in data[0]), [])
                    if not english:
                        raise ValueError('Empty prose translation')
                    parts[part_index] = english
                    fragment_path.write_text(json.dumps({'source':prose,'english':english},ensure_ascii=False),encoding='utf-8')
                    break
                except Exception:
                    if attempt == 4:
                        raise RuntimeError(f'Prose translation failed after batch error: {last_error}')
                    time.sleep(min(2**attempt,12))
        english = ''.join(parts)
        if sorted(TOKEN.findall(source)) != sorted(TOKEN.findall(english)):
            raise ValueError('Reassembled control markup differs from original')
        result[index] = english
        key = hashlib.sha256(source.encode('utf-8')).hexdigest()
        (cache/(key+'.json')).write_text(json.dumps({'source':source,'english':english},ensure_ascii=False),encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalogue', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--cache', required=True, type=Path)
    parser.add_argument('--reviewed', type=Path)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    rows = list(csv.DictReader(args.catalogue.open(encoding='utf-8-sig', newline='')))
    if args.limit:
        rows = rows[:args.limit]
    args.cache.mkdir(parents=True, exist_ok=True)
    reviewed = {r['source']: r['english'] for r in json.loads(args.reviewed.read_text(encoding='utf-8'))} if args.reviewed else {}
    unique, pending, translations = {}, [], {}
    for row in rows:
        text = row['japanese']
        if text in unique:
            continue
        index = len(unique)
        unique[text] = index
        path = args.cache / (hashlib.sha256(text.encode('utf-8')).hexdigest() + '.json')
        if text in reviewed:
            translations[index] = reviewed[text]
        elif path.exists():
            record = json.loads(path.read_text(encoding='utf-8'))
            if record['source'] != text:
                raise ValueError('Cache source mismatch')
            if JAPANESE.search(TOKEN.sub('',record['english'])):
                pending.append((index,text))
            else:
                translations[index] = record['english']
        else:
            pending.append((index, text))
    batches, batch, size = [], [], 0
    for item in pending:
        cost = len(protect(item[1])[0]) + 28
        if batch and size + cost > 1150:
            batches.append(batch)
            batch, size = [], 0
        batch.append(item)
        size += cost
        # A malformed service response must not discard unrelated dialogue.
        if len(pending) < 100:
            batches.append(batch)
            batch, size = [], 0
    if batch:
        batches.append(batch)
    print(f'{len(rows)} rows, {len(unique)} unique strings, {len(translations)} cached/reviewed, {len(batches)} batches pending.', flush=True)
    failed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(translate_batch, batch, args.cache): batch for batch in batches}
        for number, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                translations.update(future.result())
            except Exception as error:
                failed.extend(futures[future])
                print(str(error), flush=True)
            if number % 10 == 0 or number == len(batches):
                print(f'Batches {number}/{len(batches)}; translated {len(translations)}/{len(unique)}.', flush=True)
    records = []
    for row in rows:
        original = row['japanese']
        english = translations.get(unique[original])
        records.append({'address': row['address'], 'source': original, 'english': english,
                        'status': 'reviewed' if original in reviewed else 'draft' if english else 'failed'})
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    residual = sum(bool(JAPANESE.search(TOKEN.sub('', r['english'] or ''))) for r in records)
    print(f'Wrote {len(records)} rows. Failed unique strings: {len(failed)}; rows with remaining Japanese: {residual}.', flush=True)
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
