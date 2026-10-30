#!/usr/bin/env python3
"""Verify raw compiler outputs for the pinned Borsh source-path experiment.

Reads ordinary files only; no compiler, loader, VM or network operation.
Raw compiler images are compared before section-relative original data checks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

PINS = {
    'control': '09186a9021ba057d53d37b55e7d28c55415417995999c2d3e2006b943b09521a',
    'candidate': 'cd8bc6ca92d66cd9808dd8f3a3a3b27bd204f916a4b2487d8989e4b5db99bc09',
    'repeat': 'cd8bc6ca92d66cd9808dd8f3a3a3b27bd204f916a4b2487d8989e4b5db99bc09',
    'original': '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    'control_library': '93996b291f8d421c6bf9f028f984452dadfadb28570456ea4a0876e23a339b71',
    'candidate_library': '415cf04df1426d7f149f6f02f75ea593f093f36681f5dcc52077296fef6ace2d',
    'repeat_library': '415cf04df1426d7f149f6f02f75ea593f093f36681f5dcc52077296fef6ace2d',
}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def differences(old, new):
    require(len(old) == len(new), 'Length differs')
    return [(i, a, b) for i, (a, b) in enumerate(zip(old, new)) if a != b]


def sections(raw):
    require(raw[:6] == b'\x7fELF\x02\x01', 'Expected ELF64 little-endian')
    offset = struct.unpack_from('<Q', raw, 40)[0]
    size, count, names_index = struct.unpack_from('<HHH', raw, 58)
    require(size == 64 and names_index < count and offset + size * count <= len(raw), 'Invalid section table')
    table = [struct.unpack_from('<IIQQQQIIQQ', raw, offset + size * i) for i in range(count)]
    names = table[names_index]
    require(names[4] + names[5] <= len(raw), 'Invalid section-name table')
    strings = raw[names[4]:names[4] + names[5]]
    result = {}
    for row in table:
        require(row[0] < len(strings), 'Invalid section name')
        end = strings.find(b'\0', row[0])
        require(end >= 0, 'Unterminated section name')
        name = strings[row[0]:end].decode('ascii')
        if name in ['.text', '.rodata', '.data.rel.ro']:
            require(name not in result and row[4] + row[5] <= len(raw), 'Invalid section payload')
            result[name] = {'address': row[3], 'offset': row[4], 'raw': raw[row[4]:row[4] + row[5]]}
    require(len(result) == 3, 'Missing required section')
    return result


def metadata(raw):
    require(raw.startswith(b'!<arch>\n'), 'Expected archive')
    i = 8
    found = []
    while i < len(raw):
        header = raw[i:i + 60]
        require(len(header) == 60 and header[-2:] == b'`\n', 'Invalid archive header')
        size = int(header[48:58]); name = header[:16].decode().strip()
        require(i + 60 + size <= len(raw), 'Truncated member')
        if name in ['lib.rmeta/', 'lib.rmeta']:
            found.append((i + 60, raw[i + 60:i + 60 + size]))
        i += 60 + size + size % 2
    require(i == len(raw) and len(found) == 1, 'Missing or ambiguous metadata member')
    return found[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in PINS:
        parser.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    images = {name: getattr(args, name).read_bytes() for name in PINS}
    require(all(sha(images[name]) == pin for name, pin in PINS.items()), 'Input SHA-256 mismatch')
    require(images['candidate'] == images['repeat'] and images['candidate_library'] == images['repeat_library'], 'Independent repeat differs')
    old = images['control']; new = images['candidate']
    changes = differences(old, new)
    require(changes == [(1794237, 92, 47), (1794240, 92, 47)], 'Unexpected raw compiler-output changes')
    parsed = {name: sections(images[name]) for name in ['control', 'candidate', 'original']}
    require(parsed['control']['.text'] == parsed['candidate']['.text'], 'Code changed')
    require(parsed['control']['.data.rel.ro'] == parsed['candidate']['.data.rel.ro'], 'Relocated data changed')
    for name in ['control', 'candidate', 'original']:
        expected = b'src\\de\\mod.rs' if name == 'control' else b'src/de/mod.rs'
        require(parsed[name]['.rodata']['raw'][1418:1431] == expected, 'Unexpected diagnostic path')
        record = 544 if name == 'original' else 576
        data = parsed[name]['.data.rel.ro']['raw']
        zero, pointer, length, line, column = struct.unpack_from('<IIQII', data, record)
        require((zero, pointer, length, line, column) == (0, parsed[name]['.rodata']['address'] + 1418, 13, 637, 21), 'Source record differs')
    original = parsed['original']['.rodata']['raw']
    counts = {name: len(differences(original, parsed[name]['.rodata']['raw'])) for name in ['control', 'candidate']}
    require(counts == {'control': 104, 'candidate': 102}, 'Unexpected original rodata differences')
    before_offset, before = metadata(images['control_library'])
    after_offset, after = metadata(images['candidate_library'])
    require(before_offset == after_offset and len(before) == len(after), 'Metadata placement differs')
    metadata_changes = differences(before, after)
    require(len(metadata_changes) == 2 and all(a == 92 and b == 47 for _, a, b in metadata_changes), 'Unexpected metadata changes')
    require(differences(images['control_library'], images['candidate_library']) == [(before_offset + i, a, b) for i, a, b in metadata_changes], 'Non-metadata library bytes changed')
    report = {'result': 'PASS', 'inputs': PINS, 'raw_image_bytes': len(new),
              'whole_image_changes': changes, 'metadata_changes': metadata_changes,
              'text_identical': True, 'data_rel_ro_identical': True, 'whole_repeats_identical': True,
              'original_rodata_differences': counts,
              'scope': 'Two raw data bytes corrected in a pinned local compiler output. No function-match gain, formatter-gap closure, whole-original identity, native preservation or historical producer authentication.'}
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
