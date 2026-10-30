#!/usr/bin/env python3
"""Verify the PR1384 rent-helper rebase on actual current-main compiler outputs.

The controls are qualified local main1e04f5b and mainfd8b94d images. All calls are inspected
statically; no compiler, program, VM or network operation is performed.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct
import sys

ORIGINAL = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
INVENTORY = 'fb2c0a47514567d65eb45c1e268dacd5291e4659bb7dceb575a767dc20bcaff8'
SCORER = '549862761d672586123c7085c3cc61fe27137f12ca75116f07c4de5dd9e7b983'
HARNESS = {'score.py': SCORER,
           'elf_symbols.py': '7156bee72eaf1870dd1f8771a7172ea5090f6f19c1eba87ef48e05a3fb669e71',
           'llvm_tools.py': '306a50b2ba57f350e250d7c7f596ac400627ecfd24248b2291578b5ddf3fe8af'}
FRESH_HARNESS = {**HARNESS,
    'score.py': 'dbefadd7ad1ba4686c9d71186f8a7a8ca251f9685a29e3fff90881310b788076',
    'score_admission.py': '3a338337b09c2f5c6a3cd33de44e9b4ddb7c3ea77c96e8484042693f39f43c56'}
CONTROLS = {
    '72dba00e08c982f07b80d6308f73a799c19adfa72053e321b650a60a66018021': '1e04f5b34aa33c53f2b20b4200ba4ba266b4203e',
    '09186a9021ba057d53d37b55e7d28c55415417995999c2d3e2006b943b09521a': 'fd8b94dfa3a0ec671e018a5418c4b5009e26da6a'}
RENT = 0x3b598
TARGETS = [(0x13b9b8, '6buy_v211buy_handler17h'),
           (0x13f630, '6buy_v226buy_exact_quote_in_handler17h'),
           (0x144508, '14pump_recovered7sell_v217h')]


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def calls(raw, start):
    internal, syscalls = [], []
    offset = 0
    while offset < len(raw):
        insn = raw[offset:offset + 8]
        require(len(insn) == 8, 'Truncated instruction')
        if insn[0] == 0x85:
            imm = struct.unpack_from('<i', insn, 4)[0]
            if insn[1] >> 4 == 1 and imm != -1:
                internal.append({'offset': offset, 'target': start + offset + 8 + imm * 8})
            else:
                syscalls.append(insn.hex())
        offset += 16 if insn[0] == 0x18 else 8
    require(offset == len(raw), 'Truncated lddw')
    return internal, syscalls


def formatter_span(score, windows, raw, sections, physical, by_address):
    """Bind the formatter to its full callee before measuring physical intervals."""
    original_start = 0xa868
    original = windows[original_start]
    refs, _ = calls(original['raw'], original_start)
    require(len(refs) == 1, 'Unexpected original formatter references')
    target = refs[0]['target']; callee = windows[target]
    shape = (callee['bytes'], sha(callee['norm']))
    matches = []; bound = []
    for (start, size), _ in sorted(physical.items()):
        if size != original['bytes']:
            continue
        body = score.body(raw, sections, start, size)
        if score.normalize(body, start, sections) != original['norm']:
            continue
        calls_, _ = calls(body, start)
        require(len(calls_) == 1, 'Unexpected candidate formatter references')
        to = calls_[0]['target']
        row = {'start': hex(start), 'target': hex(to), 'raw_equal': body == original['raw'],
               'complete_original_callee_equal': shape in by_address[to]}
        matches.append(row)
        if row['complete_original_callee_equal']:
            bound.append((start, to))
    require(len(matches) == 7 and len(bound) == 1, 'Ambiguous formatter identity')
    start, end = bound[0]
    def partition(intervals, lo, hi):
        rows = sorted((a, size, shape) for (a, size), shape in intervals.items() if lo <= a < hi)
        cursor = lo; classes = Counter()
        for a, size, shape in rows:
            require(a == cursor and a + size <= hi, 'Gap or overlap in formatter span')
            classes[shape] += 1; cursor = a + size
        require(cursor == hi, 'Uncovered formatter span tail')
        return classes, len(rows)
    old, old_n = partition({(a, w['bytes']): (w['bytes'], sha(w['norm'])) for a, w in windows.items()}, original_start, target)
    new, new_n = partition(physical, start, end)
    removed, added = old - new, new - old
    delta = end - start - (target - original_start)
    require(sum(s[0]*n for s,n in added.items()) - sum(s[0]*n for s,n in removed.items()) == delta,
            'Physical span accounting failed')
    def rows(counter):
        return [{'bytes': s[0], 'normalized_sha256': s[1], 'count': n} for s,n in sorted(counter.items())]
    return {'original_span_bytes': target-original_start, 'candidate_span_bytes': end-start,
            'delta': delta, 'original_function_count': old_n, 'candidate_function_count': new_n,
            'gap_bytes': 0, 'normalized_candidates': matches, 'missing_classes': rows(removed),
            'extra_classes': rows(added)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ['control', 'candidate', 'repeat', 'original', 'inventory', 'harness', 'work']:
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    control_hash = sha(args.control.read_bytes())
    require(control_hash in CONTROLS, 'Unexpected local control')
    require(args.candidate.read_bytes() == args.repeat.read_bytes(), 'Whole compiler repeat differs')
    require(sha(args.original.read_bytes()) == ORIGINAL and sha(args.inventory.read_bytes()) == INVENTORY,
            'Original inputs differ')
    require(any(all(sha((args.harness / name).read_bytes()) == digest for name, digest in pins.items())
                for pins in [HARNESS, FRESH_HARNESS] if all((args.harness / name).is_file() for name in pins)),
            'Unexpected scorer dependencies')
    args.work.mkdir(parents=True, exist_ok=False)
    base = args.work / 'base'; base.mkdir()
    (base / 'original.so').write_bytes(args.original.read_bytes())
    (base / 'functions.tsv').write_bytes(args.inventory.read_bytes())
    sys.path.insert(0, str(args.harness))
    import score
    score.BASE = base
    windows = {w['start']: w for w in score.original_windows()}
    require(len(windows) == 1035, 'Incomplete original windows')
    expected_rent = (windows[RENT]['bytes'], sha(windows[RENT]['norm']))
    require(expected_rent[0] == 416, 'Unexpected original rent helper')
    images = {}
    for label, path in [('control', args.control), ('candidate', args.candidate)]:
        raw = path.read_bytes(); sections = score.sections(raw)
        functions = score.candidate_functions(path); by_address = defaultdict(set)
        physical = {}
        for start, size, name in functions:
            body = score.body(raw, sections, start, size)
            normalized = score.normalize(body, start, sections)
            shape = (size, sha(normalized))
            by_address[start].add(shape)
            physical[(start, size)] = shape
        classes = Counter(physical.values())
        bodies = {}
        for original, needle in TARGETS:
            candidates = [(st, size, name) for st, size, name in functions if needle in name]
            require(len(candidates) == 1, 'Ambiguous V2 caller')
            start, size, name = candidates[0]
            body = score.body(raw, sections, start, size)
            refs, syscalls = calls(body, start)
            original_refs, original_syscalls = calls(windows[original]['raw'], original)
            require(len(refs) == len(original_refs), 'V2 call count differs')
            require(Counter(syscalls) == Counter(original_syscalls), 'V2 syscalls differ')
            slots = [i for i, ref in enumerate(original_refs) if ref['target'] == RENT]
            require(len(slots) == 1, 'Unexpected original rent call count')
            rent_call = refs[slots[0]]
            actual_rent = by_address[rent_call['target']]
            rent_matches = expected_rent in actual_rent
            if label == 'candidate':
                require(rent_matches, f'{original:#x}: actual rent callee does not match original')
            else:
                require(not rent_matches and {size for size, _ in actual_rent} == {512}, 'Control does not reproduce duplicate-helper mismatch')
            original_shapes = [(windows[r['target']]['bytes'], sha(windows[r['target']]['norm'])) for r in original_refs]
            matched_shapes = [by_address[r['target']] & set(original_shapes) for r in refs]
            multiset_equal = all(len(s) == 1 for s in matched_shapes) and Counter(next(iter(s)) for s in matched_shapes) == Counter(original_shapes)
            ordered_equal = all(shape in by_address[ref['target']] for shape, ref in zip(original_shapes, refs))
            if label == 'candidate':
                require(multiset_equal, 'V2 complete immediate-callee multiset differs')
                if original != 0x13b9b8:
                    require(ordered_equal, 'Expected ordered callee equality absent')
            bodies[hex(original)] = {'candidate_start': hex(start), 'bytes': size, 'symbol': name,
                'normalized_sha256': sha(score.normalize(body, start, sections)),
                'normalized_equal_original': score.normalize(body, start, sections) == windows[original]['norm'],
                'calls': len(refs), 'ordered_original_callees_equal': ordered_equal,
                'original_callee_multiset_equal': multiset_equal,
                'rent_call': {'ordinal': slots[0], 'offset': rent_call['offset'], 'target': hex(rent_call['target']),
                              'actual_shapes': [{'bytes': s[0], 'normalized_sha256': s[1]} for s in sorted(actual_rent)],
                              'matches_original': rent_matches}}
        measured, image_hash = score.score_with_hash(path)
        require(image_hash == sha(raw) and set(measured) == set(windows), 'Scored input changed or incomplete')
        images[label] = {'sha256': image_hash, 'bytes': len(raw), 'classes': classes, 'score': measured,
                         'sections': sections, 'raw': raw, 'callers': bodies,
                         'formatter': formatter_span(score, windows, raw, sections, physical, by_address)}
    before, after = images['control'], images['candidate']
    membership = {}
    for field in ['normalized', 'raw']:
        old = {a for a, v in before['score'].items() if v[field]}
        new = {a for a, v in after['score'].items() if v[field]}
        require(old == new, f'{field}: changed membership')
        membership[field] = {'count': len(new), 'gains': [], 'losses': []}
    removed = before['classes'] - after['classes']; added = after['classes'] - before['classes']
    require(len(removed) == 1 and sum(removed.values()) == 1 and next(iter(removed))[0] == 512 and not added,
            'Physical normalized body changes exceed one removed 512-byte helper')
    for target, row in after['callers'].items():
        require(row['normalized_sha256'] == before['callers'][target]['normalized_sha256'], 'V2 caller body changed')
    def section_bytes(image, name):
        s = image['sections'][name]
        return image['raw'][s['offset']:s['offset'] + s['size']]
    require(before['sections']['.text']['size'] - after['sections']['.text']['size'] == 512, 'Unexpected text delta')
    require(section_bytes(before, '.rodata') == section_bytes(after, '.rodata'), 'Rodata changed')
    require(after['formatter']['delta'] - before['formatter']['delta'] == -512, 'Unexpected formatter span change')
    report = {'result': 'PASS', 'control_source_revision': CONTROLS[control_hash],
        'membership': membership, 'whole_repeat_equal': True,
        'images': {label: {k: v for k, v in image.items() if k in ['sha256', 'bytes', 'callers', 'formatter']} for label, image in images.items()},
        'removed_class': {'bytes': next(iter(removed))[0], 'normalized_sha256': next(iter(removed))[1], 'count': 1},
        'text_delta': -512, 'rodata_equal': True,
        'scope': 'Actual one-hop callee restoration with unchanged caller bodies and memberships. Buy V2 ordered callees remain unequal. No recursive/runtime equivalence, native qualification or whole-original identity follows.'}
    (args.work / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'result': 'PASS', 'membership': membership, 'text_delta': -512,
                      'rent_calls_restored': 3, 'whole_repeat_equal': True}, indent=2))


if __name__ == '__main__':
    main()
