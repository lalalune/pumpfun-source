#!/usr/bin/env python3
"""Read-only replay of the fresh-main Borsh-to-MPL producer chain.

Uses the sibling Borsh packet's bounded ELF reader and explicit checks. No
compiler, VM, loader or network operation occurs.
"""
import argparse
import importlib.util
import json
from pathlib import Path

helper = Path(__file__).resolve().parent.parent / 'borsh-producer' / 'verify_producer.py'
spec = importlib.util.spec_from_file_location('borsh_proof', helper)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
require, sha, differences, sections = b.require, b.sha, b.differences, b.sections
PINS = {
    'control': '15c29a714f16bbe749766f795d6c933d4905d4dfc9b5491942ad6b35b2d528ff',
    'borsh_only': '324d2eae8324297e645c7cdae29003333d337f876a183714f7aee5dad7e4d1f5',
    'import_only': '5087cd95257727420663f44ffece06da65d611d7c182b152377aafbafb36d97f',
    'candidate': '532aa580aa308ec42d1436306041a03fa96e67acb7265fd19e02a66acd0e5acd',
    'repeat': '532aa580aa308ec42d1436306041a03fa96e67acb7265fd19e02a66acd0e5acd',
    'original': '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    'mpl_control': 'c5f27ffec7ad6e5fe2009149d60bd0408b73341c626dd80bd8dbc7c065838a68',
    'mpl_import': 'b5578e9a34c80bfba38f4d4284d2a1e9efa2348612843c6a8144a4f5aaefb548',
    'mpl_candidate': '88d2859a9b6d0d01abfcfab62b1d26dd8a5247d850090f39b19519be7a18ef97',
    'mpl_repeat': '88d2859a9b6d0d01abfcfab62b1d26dd8a5247d850090f39b19519be7a18ef97',
}
OFFSETS = [1421, 1424, 17799, 17802, 18143, 18153, 18166]


def members(raw):
    require(raw.startswith(b'!<arch>\n'), 'Expected ar archive')
    i = 8; names = b''; result = {}
    while i < len(raw):
        header = raw[i:i + 60]
        require(len(header) == 60 and header[-2:] == b'`\n', 'Invalid ar header')
        name = header[:16].decode().strip(); size = int(header[48:58])
        payload = raw[i + 60:i + 60 + size]
        require(len(payload) == size, 'Truncated ar payload')
        if name == '//': names = payload
        if name.startswith('/') and name[1:].isdigit():
            start = int(name[1:])
            ends = [end for end in [names.find(b'/\n', start), names.find(b'\0', start)] if end >= 0]
            require(ends, 'Invalid ar long name')
            name = names[start:min(ends)].decode()
        elif name.startswith('#1/'):
            length = int(name[3:]); require(length <= size, 'Invalid BSD name')
            name = payload[:length].rstrip(b'\0').decode(); payload = payload[length:]
        if name not in ['/', '//']: name = name.rstrip('/')
        require(name not in result, 'Duplicate ar member')
        result[name] = payload; i += 60 + size + size % 2
    require(i == len(raw), 'Truncated ar padding')
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in PINS: ap.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    raw = {name: getattr(args, name).read_bytes() for name in PINS}
    require(all(sha(raw[k]) == pin for k, pin in PINS.items()), 'Input SHA-256 mismatch')
    require(raw['candidate'] == raw['repeat'] and raw['mpl_candidate'] == raw['mpl_repeat'], 'Independent repeat differs')
    parsed = {name: sections(raw[name]) for name in ['control', 'borsh_only', 'import_only', 'candidate', 'original']}
    control = parsed['control']; original = parsed['original']['.rodata']['raw']; stages = {}
    for name, count, remaining in [('control', 0, 104), ('borsh_only', 2, 102), ('import_only', 4, 100), ('candidate', 7, 97)]:
        s = parsed[name]
        changes = differences(raw['control'], raw[name])
        expected = [(control['.rodata']['offset'] + off, 92, 47) for off in OFFSETS[:count]]
        require(changes == expected, 'Unexpected whole-image changes')
        require(s['.text'] == control['.text'] and s['.data.rel.ro'] == control['.data.rel.ro'], 'Code or relocated data changed')
        require(len(differences(original, s['.rodata']['raw'])) == remaining, 'Unexpected original rodata differences')
        for off in OFFSETS[:count]: require(original[off] == s['.rodata']['raw'][off] == 47, 'Corrected byte differs from original')
        stages[name] = {'sha256':sha(raw[name]), 'bytes':len(raw[name]), 'whole_image_changes':changes,
                        'original_rodata_differences':remaining}
    archives = {name: members(raw[name]) for name in ['mpl_control', 'mpl_import', 'mpl_candidate']}
    old = archives['mpl_control']; changed = {}
    require(len(old) == 4 and 'lib.rmeta' in old, 'Unexpected MPL members')
    objects = [name for name in old if name.endswith('.o')]
    require(len(objects) == 1, 'Expected one MPL object')
    obj = objects[0]
    for name, metadata_count, object_count in [('mpl_import', 0, 2), ('mpl_candidate', 3, 5)]:
        new = archives[name]; require(new.keys() == old.keys(), 'MPL member set changed')
        rows = {key: differences(old[key], new[key]) for key in old}
        require(len(rows['lib.rmeta']) == metadata_count and len(rows[obj]) == object_count, 'Unexpected member change counts')
        require(all(not rows[key] for key in old if key not in ['lib.rmeta', obj]), 'Other ar members changed')
        require(all(a == 92 and z == 47 for values in rows.values() for _, a, z in values), 'Unexpected library byte substitutions')
        require(len(differences(raw['mpl_control'], raw[name])) == metadata_count + object_count, 'Ar headers or layout changed')
        changed[name] = rows
    report = {'result':'PASS','source_revision':'a7135a6a64c446166895f7e3ea4ca84ac1a9b848',
              'inputs':PINS,'stages':stages,'mpl_changes':changed,'independent_repeats_equal':True,
              'scope':'Seven raw section-relative data bytes corrected, including five beyond the earlier Borsh packet. No function-window gain, formatter-gap closure, native qualification or whole-original identity.'}
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'result':'PASS','remaining_rodata_differences':97,'corrected_data_bytes':7,'mpl_extra_bytes':5}))


if __name__ == '__main__': main()
