"""Generate a byte-checked native string patch from reviewed translations."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('translations', type=Path)
    parser.add_argument('header', type=Path)
    parser.add_argument('--image', type=Path, help='Validate against the original loaded image')
    args = parser.parse_args()
    image = args.image.read_bytes() if args.image else None
    records = json.loads(args.translations.read_text(encoding='utf-8'))
    lines = ['// Generated from translation/english.json. Do not edit.', '#pragma once',
             '#include <cstdint>', '#include <string_view>',
             'struct EnglishString { uint32_t address; std::string_view original; std::string_view english; };',
             'inline constexpr EnglishString kEnglishStrings[] = {']
    occupied = set()
    for record in records:
        address = int(record['address'], 0)
        original = record['source'].encode('cp932')
        # CP932 also preserves the game's controller-button markup (<○>, <×>).
        english = record['english'].encode('cp932')
        if not 0x82000400 <= address < address + len(original) + 1 <= 0x820AB20C:
            raise ValueError('Patch outside supported .rdata')
        if len(english) > len(original) or b'\0' in english:
            raise ValueError(f'English exceeds byte budget: {record["english"]}')
        span = set(range(address, address + len(original) + 1))
        if span & occupied:
            raise ValueError('Overlapping translation records')
        occupied.update(span)
        if image is not None:
            offset = address - 0x82000000
            if image[offset:offset + len(original) + 1] != original + b'\0':
                raise ValueError(f'Original bytes do not match at {address:#x}')
        expected = ''.join(f'\\x{x:02x}' for x in original)
        replacement = ''.join(f'\\x{x:02x}' for x in english)
        lines.append(f'    {{0x{address:08X}, "{expected}", "{replacement}" }},')
    lines.append('};\n')
    args.header.parent.mkdir(parents=True, exist_ok=True)
    text = '\n'.join(lines)
    if not args.header.exists() or args.header.read_text() != text:
        args.header.write_text(text, encoding='utf-8')
    print(f'Generated {len(records)} bounded string replacements' + ('; original bytes verified.' if image else '.'))


if __name__ == '__main__':
    main()
