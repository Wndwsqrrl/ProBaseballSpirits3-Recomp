"""Create a compressed XOR patch from verified original and English archives."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import struct
from pathlib import Path
from bndr import read_index

spec = importlib.util.spec_from_file_location('konami_cmp', Path(__file__).with_name('konami-cmp.py'))
cmp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cmp)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').digest()


def member(stream, entry):
    stream.seek(entry['offset'])
    result = stream.read(entry['size'])
    if len(result) != entry['size']:
        raise ValueError('Archive changed while building the patch')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('english', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.report.exists():
        parser.error('Output patch and report must be new files')
    original, english = args.original.resolve(), args.english.resolve()
    if original.samefile(english) or args.output.resolve() in (original, english):
        parser.error('Inputs and output must be different files')
    old_entries, entries = read_index(original), read_index(english)
    old_by_name = {row['name']: row for row in old_entries}
    if set(old_by_name) != {row['name'] for row in entries}:
        raise ValueError('Archive member names differ')
    old_hash, new_hash = digest(original), digest(english)
    with english.open('rb') as stream:
        header = stream.read(16)
        directory_size = struct.unpack_from('>I', header, 8)[0] * 2048
        stream.seek(0)
        directory = stream.read(directory_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    changed = []
    with original.open('rb') as source, english.open('rb') as target, args.output.open('xb') as output:
        with gzip.GzipFile(filename='', mode='wb', fileobj=output, compresslevel=6, mtime=0) as patch:
            patch.write(b'P3ENG001')
            patch.write(struct.pack('<Q', original.stat().st_size) + old_hash)
            patch.write(struct.pack('<Q', english.stat().st_size) + new_hash)
            patch.write(struct.pack('<I', len(directory)) + directory)
            patch.write(struct.pack('<I', len(entries)))
            for index, row in enumerate(entries):
                old = old_by_name[row['name']]
                before, after = member(source, old), member(target, row)
                mode = int(before != after)
                patch.write(struct.pack('<QIQIB', old['offset'], old['size'], row['offset'], row['size'], mode))
                if mode:
                    decoded = cmp.decompress(before) if before.startswith(b'CMP\0') else before
                    if len(decoded) != len(after) or len(after) > 64 * 1024 * 1024:
                        raise ValueError(f'Unsupported decoded patch extent: {row["name"]}')
                    patch.write(bytes(a ^ b for a, b in zip(decoded, after)))
                    changed.append(row['name'])
                if (index + 1) % 400 == 0:
                    print(f'{index + 1}/{len(entries)} members encoded', flush=True)
    report = dict(format='P3ENG001 / gzip / decoded XOR', source_size=original.stat().st_size,
                  source_sha256=old_hash.hex(), target_size=english.stat().st_size,
                  target_sha256=new_hash.hex(), archive_members=len(entries),
                  unchanged_members=len(entries)-len(changed), changed_members=changed,
                  patch_size=args.output.stat().st_size, patch_sha256=digest(args.output).hex(),
                  original_files_unchanged=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(f'Created delta for {len(changed)} changed members ({args.output.stat().st_size:,} bytes).', flush=True)


if __name__ == '__main__':
    main()
