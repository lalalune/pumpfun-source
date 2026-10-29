#!/usr/bin/env python3
"""Statically rescore two real builds and check sweep's complete callee multiset.

Build the pinned base and this branch using the normal identity recipe first.
This script neither builds nor executes either program. --work must be new.
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
ORIGINAL_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
WINDOWS_SHA256 = 'fb2c0a47514567d65eb45c1e268dacd5291e4659bb7dceb575a767dc20bcaff8'
TARGET = 0x72810


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', required=True, type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--repeat', type=Path)
    parser.add_argument('--original', type=Path, default=ROOT / 'evidence/original/pump/deployed.so')
    parser.add_argument('--objdump', help='Override only the official scorer objdump executable path.')
    parser.add_argument('--work', required=True, type=Path, help='New directory for fresh original cache and report.')
    args = parser.parse_args()
    original = args.original.read_bytes()
    inventory = (ROOT / 'reconstruction/base/functions.tsv').read_bytes()
    require(digest(original) == ORIGINAL_SHA256, 'Unexpected original allocation capture')
    require(digest(inventory) == WINDOWS_SHA256, 'Unexpected original window inventory')
    args.work.mkdir(parents=True, exist_ok=False)
    base = args.work / 'base'
    base.mkdir()
    (base / 'original.so').write_bytes(original)
    (base / 'functions.tsv').write_bytes(inventory)
    harness = ROOT / 'reconstruction/harness'
    sys.path.insert(0, str(harness))
    import score
    score.BASE = base
    if args.objdump:
        score.OBJDUMP = args.objdump
    import win

    windows = {w['start']: w for w in score.original_windows()}
    require(len(windows) == 1035, 'Incomplete original inventory')
    target = windows[TARGET]

    def calls(raw, start):
        internal, external = [], []
        offset = 0
        while offset < len(raw):
            instruction = raw[offset:offset + 8]
            require(len(instruction) == 8, 'Truncated instruction')
            if instruction[0] == 0x85:
                imm = struct.unpack_from('<i', instruction, 4)[0]
                if instruction[1] >> 4 == 1 and imm != -1:
                    internal.append(start + offset + 8 + imm * 8)
                else:
                    external.append(instruction.hex())
            offset += 16 if instruction[0] == 0x18 else 8
        require(offset == len(raw), 'Truncated lddw')
        return internal, external

    original_calls, original_syscalls = calls(target['raw'], TARGET)
    expected = Counter((windows[a]['bytes'], digest(windows[a]['norm'])) for a in original_calls)
    original_tokens = [row[2] for row in win.insns(target['raw'], TARGET, win.ORIG_SECS)]
    reports, scores = {}, {}
    for label, path in [('control', args.control), ('candidate', args.candidate)]:
        image = path.read_bytes()
        sections = score.sections(image)
        functions = score.candidate_functions(path)
        by_address = defaultdict(list)
        for start, length, name in functions:
            by_address[start].append((length, name))
        selected = [(s, n, name) for s, n, name in functions if '5sweep7execute17h' in name]
        require(len(selected) == 1, 'Sweep symbol is missing or ambiguous')
        start, length, symbol = selected[0]
        raw = score.body(image, sections, start, length)
        direct, syscalls = calls(raw, start)
        actual, bindings = Counter(), []
        for address in direct:
            possibilities = set()
            for size, name in by_address[address]:
                body = score.body(image, sections, address, size)
                possibilities.add((size, digest(score.normalize(body, address, sections))))
            matched = possibilities & set(expected)
            require(len(matched) == 1, f'{label}: callee {address:#x} has no unique full original-body binding')
            key = next(iter(matched))
            actual[key] += 1
            bindings.append({'address': hex(address), 'bytes': key[0], 'normalized_sha256': key[1], 'all_symbols': by_address[address]})
        require(actual == expected, f'{label}: complete normalized callee multiset differs')
        require(Counter(syscalls) == Counter(original_syscalls), f'{label}: syscall instructions differ')
        tokens = [row[2] for row in win.insns(raw, start, sections)]
        scores[label] = score.score(path)
        reports[label] = {
            'image_bytes': len(image), 'image_sha256': digest(image),
            'normalized': sum(v['normalized'] for v in scores[label].values()),
            'raw': sum(v['raw'] for v in scores[label].values()),
            'sweep': {'symbol': symbol, 'address': hex(start), 'bytes': length,
                      'ratio': round(difflib.SequenceMatcher(None, original_tokens, tokens, autojunk=False).ratio(), 5),
                      'internal_calls': len(direct), 'syscalls': len(syscalls),
                      'callee_body_multiset_equal': True, 'bindings': bindings},
        }
    changes = {}
    for field in ['normalized', 'raw']:
        before = {a for a, value in scores['control'].items() if value[field]}
        after = {a for a, value in scores['candidate'].items() if value[field]}
        changes[field] = {'gains': [hex(a) for a in sorted(after - before)], 'losses': [hex(a) for a in sorted(before - after)]}
        require(not changes[field]['losses'], f'{field} membership lost')
    require(reports['candidate']['sweep']['ratio'] > reports['control']['sweep']['ratio'], 'Sweep ratio did not improve')
    if args.repeat:
        require(args.repeat.read_bytes() == args.candidate.read_bytes(), 'Repeated complete compiler output differs')
    report = {'result': 'PASS', 'original_sha256': digest(original), 'original_sweep_bytes': target['bytes'],
              'images': reports, 'membership': changes, 'repeat_exact': True if args.repeat else None,
              'harness_sha256': {name: digest((harness / name).read_bytes()) for name in ['score.py', 'win.py']},
              'scope': 'Partial source reconstruction. Complete immediate-callee bodies are compared as a multiset, not ordered or recursive behavior. Raw window counts do not establish whole-file identity. No program execution.'}
    (args.work / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'result': report['result'], 'images': {k: {**{f: v[f] for f in ['image_sha256', 'normalized', 'raw']}, 'sweep_ratio': v['sweep']['ratio']} for k, v in reports.items()}, 'membership': changes, 'repeat_exact': report['repeat_exact']}, indent=2))


if __name__ == '__main__':
    main()
