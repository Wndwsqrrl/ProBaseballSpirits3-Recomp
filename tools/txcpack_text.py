"""Replace reviewed strings in the original TXCPACK record slots."""
import json
import struct


def load_packed_text(path):
    return json.loads(path.read_text(encoding='utf-8')) if path else {}


def patch_packed_text(data, edits):
    if data[:4] != b'CHK ' or struct.unpack_from('>I', data, 12)[0] != len(data):
        raise ValueError('Invalid CHK container for packed text')

    chunks = {}
    offset = 16
    while offset + 16 <= len(data) and data[offset:offset+8] != b'CHUNKEND':
        allocated, actual = struct.unpack_from('>II', data, offset + 8)
        payload = offset + 16
        if allocated < 16 or actual > allocated - 16 or offset + allocated > len(data):
            raise ValueError(f'Invalid CHK chunk at {offset:#x}')
        if data[payload:payload+8] == b'TXCPACK ':
            chunks[offset] = memoryview(data)[payload:payload+actual]
        offset += allocated

    patched = bytearray(data)
    seen = set()
    for edit in edits:
        chunk_offset, entry = int(edit['chunk'], 16), edit['entry']
        label = f'{chunk_offset:#x} entry {entry}'
        if (chunk_offset, entry) in seen or chunk_offset not in chunks:
            raise ValueError(f'Duplicate or missing TXCPACK record at {label}')
        seen.add((chunk_offset, entry))
        chunk = chunks[chunk_offset]
        rect_count, rect_table, count, ptr_table = struct.unpack_from('>4I', chunk, 28)
        table_end = ptr_table + 4 * count
        if rect_table + 8 * rect_count != ptr_table or not table_end <= len(chunk):
            raise ValueError(f'Invalid TXCPACK tables at {label}')
        if not 0 <= entry < count:
            raise ValueError(f'TXCPACK entry outside table at {label}')
        record = struct.unpack_from('>I', chunk, ptr_table + 4 * entry)[0]
        limit = (struct.unpack_from('>I', chunk, ptr_table + 4 * (entry + 1))[0]
                 if entry + 1 < count else len(chunk))
        if not table_end <= record < record + 28 <= limit <= len(chunk):
            raise ValueError(f'Invalid TXCPACK record extent at {label}')
        opcode, = struct.unpack_from('>I', chunk, record)
        pointer = {4: 24, 5: 32}.get(opcode)
        if pointer is None or record + pointer + 4 > limit:
            raise ValueError(f'Unsupported TXCPACK text record at {label}')
        position, = struct.unpack_from('>I', chunk, record + pointer)
        if not record + pointer + 4 <= position < limit:
            raise ValueError(f'TXCPACK text pointer outside record at {label}')

        original = bytes.fromhex(edit['source_hex'])
        end = position + len(original)
        if not original or b'\0' in original or end >= limit or chunk[position:end+1] != original + b'\0':
            raise ValueError(f'Unexpected original TXCPACK text at {label}')
        english = edit['english'].encode('ascii')
        if any(not 32 <= c <= 126 for c in english):
            raise ValueError(f'Invalid English TXCPACK text at {label}')
        stop = position + max(len(original), len(english)) + 1
        if stop > limit or any(chunk[end+1:stop]):
            raise ValueError(f'English TXCPACK text exceeds original slot at {label}')
        start = chunk_offset + 16 + position
        patched[start:start+stop-position] = (english + b'\0').ljust(stop-position, b'\0')
    return bytes(patched)
