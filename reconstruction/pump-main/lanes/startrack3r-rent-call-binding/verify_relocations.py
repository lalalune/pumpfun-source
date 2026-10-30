#!/usr/bin/env python3
"""Read-only data-reference check for the recorded PR1384 compiler experiment.

Legacy EM_SBPF/e_flags=0 relative data relocations carry the low address in
bytes 4..8 of the relocation slot. No ELF is loaded, patched or executed.
The paired data graph is checked against the local control, not authenticated
as original-program data; code terminals use complete normalized bodies only.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_rent_edges import CONTROLS, FRESH_HARNESS, INVENTORY, ORIGINAL, require, sha


def data_slots(raw, sections):
    require(struct.unpack_from('<H', raw, 18)[0] == 263, 'Expected EM_SBPF')
    require(struct.unpack_from('<I', raw, 48)[0] == 0, 'Unsupported ELF flags')
    data = sections['.data.rel.ro']; rel = sections['.rel.dyn']
    require(data['addr'] == data['offset'], 'Unsupported virtual address mapping')
    require(rel['size'] % 16 == 0, 'Truncated relocation table')
    contents = raw[data['offset']:data['offset'] + data['size']]
    scalars = bytearray(contents); slots = {}
    for p in range(rel['offset'], rel['offset'] + rel['size'], 16):
        address, info = struct.unpack_from('<QQ', raw, p)
        if not data['addr'] <= address < data['addr'] + data['size']:
            continue
        offset = address - data['addr']
        require(info == 8, 'Unexpected data relocation type or symbol')
        require(offset % 8 == 0 and offset + 8 <= len(contents), 'Invalid data slot')
        require(offset not in slots, 'Duplicate data slot')
        low, value = struct.unpack_from('<II', contents, offset)
        require(low == 0, 'Nonzero reserved low word in legacy slot')
        slots[offset] = value
        scalars[offset:offset + 8] = bytes(8)
    require(len(slots) == 590, 'Unexpected data-relocation count')
    return contents, slots, bytes(scalars)


def pointer_section(sections, value):
    found = [(name, value - s['addr']) for name, s in sections.items()
             if s['addr'] > 0 and s['addr'] <= value < s['addr'] + s['size']]
    require(len(found) <= 1, 'Ambiguous pointer section')
    return found[0] if found else None


def code_data_refs(body, start, sections, by_address, relocations):
    refs = []; i = 0
    while i < len(body):
        require(i + 8 <= len(body), 'Truncated instruction')
        if body[i] == 0x18:
            require(i + 16 <= len(body), 'Truncated LDDW')
            value = struct.unpack_from('<I', body, i + 4)[0] | struct.unpack_from('<I', body, i + 12)[0] << 32
            if start + i in relocations:
                require(relocations[start + i] == 8, 'Unexpected LDDW relocation')
                section = pointer_section(sections, value)
                require(section and section[0] in ['.text', '.rodata', '.data.rel.ro'], 'Unexpected LDDW referent')
                if section[0] == '.text':
                    require(by_address[value], 'LDDW code referent is not a complete function')
                    refs.append((i, '.text', tuple(sorted(by_address[value]))))
                else:
                    refs.append((i, *section))
            else:
                refs.append((i, 'unrelocated-value', value))
            i += 16
        else:
            i += 8
    return tuple(refs)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ['control', 'candidate', 'original', 'inventory', 'harness', 'work']:
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    require(sha(args.control.read_bytes()) in CONTROLS, 'Unexpected local control')
    require(sha(args.original.read_bytes()) == ORIGINAL and sha(args.inventory.read_bytes()) == INVENTORY,
            'Original inputs differ')
    require(all(sha((args.harness / name).read_bytes()) == digest for name, digest in FRESH_HARNESS.items()),
            'Unexpected scorer dependencies')
    args.work.mkdir(parents=True, exist_ok=False)
    base = args.work / 'base'; base.mkdir()
    (base / 'original.so').write_bytes(args.original.read_bytes())
    (base / 'functions.tsv').write_bytes(args.inventory.read_bytes())
    sys.path.insert(0, str(args.harness)); import score
    score.BASE = base
    images = {}
    for name, path in [('control', args.control), ('candidate', args.candidate)]:
        raw = path.read_bytes(); sections = score.sections(raw)
        contents, slots, scalars = data_slots(raw, sections)
        physical = {}; by_address = defaultdict(set); signatures = defaultdict(Counter)
        rel = sections['.rel.dyn']
        relocation_rows = [struct.unpack_from('<QQ', raw, p) for p in range(rel['offset'], rel['offset'] + rel['size'], 16)]
        relocations = dict(relocation_rows)
        require(len(relocations) == len(relocation_rows), 'Duplicate relocation location')
        for start, size, symbol in score.candidate_functions(path):
            if (start, size) in physical:
                continue
            body = score.body(raw, sections, start, size)
            shape = (size, sha(score.normalize(body, start, sections)))
            physical[(start, size)] = shape; by_address[start].add(shape)
        for (start, size), shape in physical.items():
            body = score.body(raw, sections, start, size)
            signatures[shape][code_data_refs(body, start, sections, by_address, relocations)] += 1
        relative_code_refs = sum(sum(ref[1] != 'unrelocated-value' for ref in refs) * n
                                 for group in signatures.values() for refs, n in group.items())
        require(relative_code_refs + len(slots) == sum(info == 8 for info in relocations.values()),
                'Relative relocations are not fully covered by code and data')
        measured, digest = score.score_with_hash(path)
        require(digest == sha(raw) and len(measured) == 1035, 'Input changed or score domain incomplete')
        images[name] = dict(raw=raw, sections=sections, contents=contents, slots=slots, scalars=scalars,
                            physical=physical, by_address=by_address, signatures=signatures, measured=measured, sha256=digest)
    old, new = images['control'], images['candidate']
    require(old['slots'].keys() == new['slots'].keys(), 'Data relocation positions changed')
    require(old['scalars'] == new['scalars'], 'Non-relocation data bytes changed')
    def section(image, name):
        s = image['sections'][name]
        return image['raw'][s['offset']:s['offset'] + s['size']]
    require(section(old, '.rodata') == section(new, '.rodata'), 'Rodata changed')
    rows = []
    for offset, before in old['slots'].items():
        after = new['slots'][offset]
        left = pointer_section(old['sections'], before); right = pointer_section(new['sections'], after)
        require(left and right and left[0] == right[0], 'Relocation target section changed')
        if left[0] == '.text':
            shapes = old['by_address'][before]
            require(shapes and shapes == new['by_address'][after], 'Complete code referent changed')
            binding = {'section': '.text', 'shapes': [{'bytes': n, 'normalized_sha256': h} for n, h in sorted(shapes)]}
        else:
            require(left[0] in ['.rodata', '.data.rel.ro'] and left == right, 'Data target offset changed')
            binding = {'section': left[0], 'offset': left[1]}
        rows.append({'slot_offset': offset, 'control_value': hex(before), 'candidate_value': hex(after), 'binding': binding})
    old_classes, new_classes = Counter(old['physical'].values()), Counter(new['physical'].values())
    removed = old_classes - new_classes; added = new_classes - old_classes
    require(not added and removed == Counter({(512, '7637ff7ad48c6a6bfd93706a84e61be73c4e22c4b9ecad061e4b034ebeb93952'): 1}),
            'Unexpected physical function-class change')
    retained_classes = []
    for shape, count in new_classes.items():
        require(old['signatures'][shape] == new['signatures'][shape], 'Retained body class data references changed')
        retained_classes.append({'bytes': shape[0], 'normalized_sha256': shape[1], 'physical_occurrences': count,
            'relocated_lddw_references': sum(sum(r[1] != 'unrelocated-value' for r in refs) * n for refs, n in new['signatures'][shape].items()),
            'unrelocated_lddw_values': sum(sum(r[1] == 'unrelocated-value' for r in refs) * n for refs, n in new['signatures'][shape].items())})
    membership = {}
    for field in ['normalized', 'raw']:
        before = {a for a, row in old['measured'].items() if row[field]}
        after = {a for a, row in new['measured'].items() if row[field]}
        require(before == after, 'Membership changed')
        membership[field] = len(after)
    report = {'result': 'PASS', 'images': {k: v['sha256'] for k, v in images.items()}, 'membership': membership,
        'encoding': 'EM_SBPF=263, e_flags=0, REL type8/symbol0; low address in u32 at slot+4, reserved u32 at slot+0 is zero',
        'slots': len(rows), 'target_counts': dict(Counter(r['binding']['section'] for r in rows)),
        'changed_slots': sum(r['control_value'] != r['candidate_value'] for r in rows),
        'rodata_equal': True, 'all_non_relocation_data_bytes_equal': True,
        'physical_retained_functions': sum(new_classes.values()), 'retained_normalized_classes': len(new_classes),
        'retained_relocated_lddw_references': sum(r['relocated_lddw_references'] for r in retained_classes),
        'retained_unrelocated_lddw_values': sum(r['unrelocated_lddw_values'] for r in retained_classes),
        'rows': rows, 'retained_classes': sorted(retained_classes, key=lambda r: (r['bytes'], r['normalized_sha256'])),
        'scope': 'Control-to-candidate data graph, including all retained physical function-class data-reference signatures as multisets. Code terminals use complete normalized bodies; their direct calls are not recursively verified. Not original data equality, raw-image identity, runtime equivalence, or a native recipe qualification.'}
    (args.work / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['rows', 'retained_classes']}, indent=2))


if __name__ == '__main__':
    main()
