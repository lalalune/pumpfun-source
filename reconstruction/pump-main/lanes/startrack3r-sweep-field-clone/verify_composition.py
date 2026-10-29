#!/usr/bin/env python3
"""Check the two-source composition against real compiler outputs, without execution.

Requires both new raw gains, the execute-buy normalized gain, no lost membership,
complete immediate-callee multiplicities, exact syscall instructions and a repeat.
"""
import argparse
from collections import Counter, defaultdict
import difflib
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[4]
ORIGINAL = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
INVENTORY = 'fb2c0a47514567d65eb45c1e268dacd5291e4659bb7dceb575a767dc20bcaff8'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def calls(raw, start):
    internal, external = [], []
    offset = 0
    while offset < len(raw):
        x = raw[offset:offset + 8]
        require(len(x) == 8, 'Truncated instruction')
        if x[0] == 0x85:
            imm = struct.unpack_from('<i', x, 4)[0]
            if x[1] >> 4 == 1 and imm != -1:
                internal.append(start + offset + 8 + imm * 8)
            else:
                external.append(x.hex())
        offset += 16 if x[0] == 0x18 else 8
    require(offset == len(raw), 'Truncated lddw')
    return internal, external


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['control', 'candidate', 'repeat', 'work']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--original', type=Path, default=ROOT / 'evidence/original/pump/deployed.so')
    parser.add_argument('--inventory', type=Path, default=ROOT / 'reconstruction/base/functions.tsv')
    parser.add_argument('--harness', type=Path, default=ROOT / 'reconstruction/harness')
    parser.add_argument('--objdump', required=True)
    args = parser.parse_args()
    original, inventory = args.original.read_bytes(), args.inventory.read_bytes()
    require(digest(original) == ORIGINAL and digest(inventory) == INVENTORY, 'Unexpected original inputs')
    require(args.candidate.read_bytes() == args.repeat.read_bytes(), 'Complete compiler repeat differs')
    args.work.mkdir(parents=True, exist_ok=False)
    base = args.work / 'base'; base.mkdir()
    (base / 'original.so').write_bytes(original)
    (base / 'functions.tsv').write_bytes(inventory)
    sys.path.insert(0, str(args.harness))
    import score
    score.BASE = base
    score.OBJDUMP = args.objdump
    import win
    windows = {w['start']: w for w in score.original_windows()}
    require(len(windows) == 1035, 'Incomplete original inventory')
    targets = [(0x83c00, '5trade14v3_execute_buy17h'), (0x5b3b0, '15multi_hop_curve8swap_hop17h')]
    reports, scores = {}, {}
    for label, path in [('control', args.control), ('candidate', args.candidate)]:
        image = path.read_bytes(); sections = score.sections(image)
        fs = score.candidate_functions(path)
        by_address = defaultdict(list)
        for st, size, name in fs:
            by_address[st].append((size, name))

        def shapes(address):
            return {(size, digest(score.normalize(score.body(image, sections, address, size), address, sections)))
                    for size, _ in by_address[address]}

        measured = {}
        for address, needle in targets:
            original_window = windows[address]
            oc, os = calls(original_window['raw'], address)
            expected = Counter((windows[x]['bytes'], digest(windows[x]['norm'])) for x in oc)
            selected = [(st, size, name) for st, size, name in fs if needle in name]
            require(len(selected) == 1, 'Target symbol missing or ambiguous')
            st, size, name = selected[0]
            raw = score.body(image, sections, st, size)
            cc, cs = calls(raw, st); actual = Counter(); bindings = []
            for to in cc:
                matched = shapes(to) & set(expected)
                require(len(matched) == 1, f'{label}: unresolved complete callee shape at {to:#x}')
                shape = next(iter(matched)); actual[shape] += 1
                bindings.append({'start': hex(to), 'bytes': shape[0], 'normalized_sha256': shape[1],
                                 'symbols': by_address[to]})
            require(actual == expected, f'{label}: complete callee multiset differs for {address:#x}')
            require(Counter(cs) == Counter(os), f'{label}: syscall instructions differ')
            ot = [r[2] for r in win.insns(original_window['raw'], address, win.ORIG_SECS)]
            ct = [r[2] for r in win.insns(raw, st, sections)]
            measured[hex(address)] = {'start': hex(st), 'bytes': size, 'symbol': name,
                'normalized_equal': score.normalize(raw, st, sections) == original_window['norm'],
                'ratio': round(difflib.SequenceMatcher(None, ot, ct, autojunk=False).ratio(), 5),
                'internal_calls': len(cc), 'syscalls': len(cs), 'callee_bindings': bindings}
        scores[label] = score.score(path)
        report = {'sha256': digest(image), 'bytes': len(image), 'targets': measured,
                  'normalized': sum(x['normalized'] for x in scores[label].values()),
                  'raw': sum(x['raw'] for x in scores[label].values())}
        if label == 'candidate':
            gains = {}
            for address in [0xa7b0, 0xa868]:
                w = windows[address]; oc, os = calls(w['raw'], address)
                require(len(oc) == 1 and not os, 'Unexpected original raw-gain call shape')
                expected = (windows[oc[0]]['bytes'], digest(windows[oc[0]]['norm']))
                matches = {}
                for st, size, name in fs:
                    if size != w['bytes'] or score.body(image, sections, st, size) != w['raw']:
                        continue
                    cc, cs = calls(w['raw'], st)
                    require(len(cc) == 1 and not cs and expected in shapes(cc[0]),
                            f'Raw-equal wrapper {address:#x} has a different callee shape')
                    matches[st] = {'start': hex(st), 'bytes': size, 'raw_sha256': digest(w['raw']),
                                   'callee_start': hex(cc[0]), 'callee_bytes': expected[0],
                                   'callee_normalized_sha256': expected[1],
                                   'span_bytes': cc[0] - st, 'original_span_bytes': oc[0] - address}
                require(matches, f'Missing complete raw gain {address:#x}')
                gains[hex(address)] = list(matches.values())
            report['bound_raw_gains'] = gains
        reports[label] = report
    changes = {}
    for field in ['normalized', 'raw']:
        before = {a for a, v in scores['control'].items() if v[field]}
        after = {a for a, v in scores['candidate'].items() if v[field]}
        require(not before - after, f'{field}: membership loss')
        gains = after - before
        require(gains == ({0x83c00} if field == 'normalized' else {0xa7b0, 0xa868}),
                f'{field}: expected integration gains absent or changed')
        changes[field] = {'gains': [hex(a) for a in sorted(gains)], 'losses': []}
    require(reports['candidate']['targets']['0x83c00']['normalized_equal'], 'Execute-buy does not match')
    require(reports['candidate']['targets']['0x5b3b0']['ratio'] > reports['control']['targets']['0x5b3b0']['ratio'],
            'Swap target did not improve')
    report = {'result': 'PASS', 'images': reports, 'membership': changes, 'repeat_exact': True,
              'harness_sha256': {n: digest((args.harness / n).read_bytes()) for n in ['score.py', 'win.py']},
              'scope': 'Measured compiler outputs only. No source provenance, recursive/runtime equivalence, native-host preservation or whole-original identity follows from this static check.'}
    (args.work / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result': 'PASS', 'counts': {k: {n: v[n] for n in ['normalized', 'raw', 'sha256']}
                                                for k, v in reports.items()}, 'membership': changes,
                      'repeat_exact': True}, indent=2))


if __name__ == '__main__':
    main()
