"""Package the verified Windows preview using an explicit file allowlist."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
import zipfile


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    if not re.fullmatch(r'v\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?', args.version):
        parser.error('Use a version such as v0.1.0-preview.1')
    if args.output.exists():
        parser.error('Output ZIP already exists; use a new artifact path')
    files = {}
    for name in ['ProSpi3 Launcher.exe', 'bin/prospi3.exe', 'bin/rexruntime.dll', 'bin/rexgpu-xenos.dll', 'assets/english-assets.p3patch']:
        path = args.stage / name
        if not path.is_file():
            parser.error(f'Required release file is missing: {name}')
        files[name] = path
    for name in ['README.md', 'CHANGELOG.md', 'NOTICES.md']:
        files[name] = root / name
    files['README.md'] = root / 'docs/release-README.md'
    for name in ['getting-started.md', 'known-issues.md', 'screenshots.md']:
        files['docs/' + name] = root / 'docs' / name
    files['docs/images/launcher.png'] = root / 'docs/images/launcher.png'
    for name in ['hanshin-introduction.png', 'main-menu.png', 'lineup.png']:
        files['docs/images/' + name] = root / 'docs/images' / name
    files['licenses/game-logo-NOTICE.txt'] = root / 'launcher/assets/NOTICE.txt'
    for path in sorted((root / 'licenses').rglob('*')):
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path
    for name, path in files.items():
        if not path.is_file() or any(part.lower() in ['local', '.git', 'userdata', 'cache'] for part in Path(name).parts) or path.suffix.lower() in ['.xex', '.fbd', '.chk', '.iso']:
            raise ValueError(f'Unsafe or missing package input: {name}')
    readme = files['README.md'].read_bytes().replace(b'(getting-started.md)', b'(docs/getting-started.md)').replace(b'(known-issues.md)', b'(docs/known-issues.md)').replace(b'(screenshots.md)', b'(docs/screenshots.md)').replace(b'(images/', b'(docs/images/').replace(b'(../NOTICES.md)', b'(NOTICES.md)')
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    metadata = dict(version=args.version, source_commit=source_commit, platform='Windows x64', language_default='English',
                    languages=['English', 'Japanese'], original_game_required=True,
                    files={name: dict(size=len(readme), sha256=hashlib.sha256(readme).hexdigest()) if name == 'README.md'
                           else dict(size=path.stat().st_size, sha256=sha(path)) for name, path in files.items()})
    prefix = 'ProSpi3-Recomp-' + args.version + '-win64/'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in files.items():
            if name == 'README.md':
                archive.writestr(prefix + name, readme)
            else:
                archive.write(path, prefix + name, compress_type=zipfile.ZIP_STORED if name.endswith('.p3patch') else zipfile.ZIP_DEFLATED)
        archive.writestr(prefix + 'release-manifest.json', json.dumps(metadata, indent=2)+'\n')
    with zipfile.ZipFile(args.output) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {prefix + n for n in files} | {prefix + 'release-manifest.json'}
        for name, item in metadata['files'].items():
            assert hashlib.sha256(archive.read(prefix + name)).hexdigest() == item['sha256']
    checksum = args.output.parent / 'SHA256SUMS.txt'
    checksum.write_text(sha(args.output) + '  ' + args.output.name + '\n', encoding='ascii', newline='\n')
    args.output.with_suffix('.manifest.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(f'Verified {len(files)} packaged files; {args.output.stat().st_size:,} bytes. Original game data and local profiles excluded.')


if __name__ == '__main__':
    main()
