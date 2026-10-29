#!/usr/bin/env python3
"""Recompute official memberships and bounded caller diagnostics for two fresh ELFs."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import struct
import sys

TARGETS = {0x14a8a8: ('pump_recovered::trade::sell',) * 2}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[4])
    ap.add_argument('--control', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--objdump', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / 'reconstruction/harness'))
    import score
    import win
    score.OBJDUMP = win.OBJDUMP = str(a.objdump.resolve())
    original = (score.BASE / 'original.so').read_bytes()
    os = score.sections(original)
    windows = {w['start']: w for w in score.original_windows()}
    original_map = {s: (w['bytes'], '') for s, w in windows.items()}

    def edges(blob, secs, start, size, mapping):
        raw = score.body(blob, secs, start, size)
        result = []
        off = 0
        while off < len(raw):
            op, regs, _, imm = struct.unpack_from('<BBhi', raw, off)
            if op == 0x85:
                if regs >> 4 != 1 or imm == -1:
                    result.append(['syscall', imm])
                else:
                    target = start + off + 8 + imm * 8
                    n, _ = mapping[target]
                    body = score.body(blob, secs, target, n)
                    result.append([n, digest(score.normalize(body, target, secs))])
            off += 16 if op == 0x18 else 8
        return result

    analyses = []
    for which, path in enumerate((a.control, a.candidate)):
        blob = path.read_bytes()
        secs = score.sections(blob)
        funcs = score.candidate_functions(path)
        mapping = {s: (n, sym) for s, n, sym in funcs}
        matches = score.score(path)
        rows = {}
        for start, names in TARGETS.items():
            picked = [(s, n) for s, n, sym in funcs if win.demangle(sym) == names[which]]
            if len(picked) != 1:
                raise ValueError(f'Expected one {names[which]}, got {len(picked)}')
            s, n = picked[0]
            raw = score.body(blob, secs, s, n)
            norm = score.normalize(raw, s, secs)
            w = windows[start]
            ot = [x[2] for x in win.insns(w['raw'], start, os)]
            ct = [x[2] for x in win.insns(raw, s, secs)]
            calls = edges(blob, secs, s, n, mapping)
            ocalls = edges(original, os, start, w['bytes'], original_map)
            rows[hex(start)] = {
                'symbol': names[which], 'original_bytes': w['bytes'], 'candidate_bytes': n,
                'normalized_equal': norm == w['norm'],
                'differing_normalized_slots': [hex(i) for i in range(0, n, 8) if norm[i:i+8] != w['norm'][i:i+8]] if n == w['bytes'] else None,
                'diagnostic_ratio': round(difflib.SequenceMatcher(None, ot, ct, autojunk=False).ratio(), 6),
                'calls': calls, 'ordered_callees_equal_original': calls == ocalls,
            }
        analyses.append({
            'elf_sha256': digest(blob),
            'memberships': {field: [hex(s) for s, row in matches.items() if row[field]]
                            for field in ('normalized', 'raw')},
            'targets': rows,
        })
    control, candidate = analyses
    delta = {}
    for field in ('normalized', 'raw'):
        before, after = (set(x['memberships'][field]) for x in analyses)
        delta[field] = {'before': len(before), 'after': len(after),
                        'gains': sorted(after - before), 'losses': sorted(before - after)}
    for start in TARGETS:
        key = hex(start)
        b, c = control['targets'][key], candidate['targets'][key]
        c['ordered_callees_equal_control'] = c['calls'] == b['calls']
        for row in (b, c):
            calls = row.pop('calls')
            row['call_count'] = len(calls)
            row['ordered_callee_signatures_sha256'] = digest(json.dumps(calls, separators=(',', ':')).encode())
    passed = (all(not d['losses'] for d in delta.values()) and
              all(r['ordered_callees_equal_control'] and r['ordered_callees_equal_original'] and r['call_count'] == 47 for r in candidate['targets'].values()))
    report = {'scope': 'Static source-build comparison; no runtime execution or new full-window gain implied.',
              'original_sha256': digest(original), 'control': control, 'candidate': candidate,
              'delta': delta, 'checks_passed': passed}
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'delta': delta, 'checks_passed': passed}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
