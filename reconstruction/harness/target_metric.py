#!/usr/bin/env python3
"""Measure how close a candidate build is to one original window.

  target_metric.py <unstripped.so> <orig_start> [--sym REGEX] [--top N] [--slots N]

For each candidate function (those whose symbol matches --sym, else the closest by
opcode n-grams) prints one JSON line: size, normalized/raw equality, the instruction
ratio used by win.py, the differing normalized 8-byte slots when sizes are equal, and
direct-call / syscall counts. Lower `slots_diff` and higher `ratio` mean closer; only
score.py decides acceptance.
"""
import argparse
import difflib
import json
import re
import struct
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
from score import sections, normalize, body, candidate_functions, original_windows  # noqa: E402
from win import Cand, insns, demangle, best_candidates, ORIG, ORIG_SECS  # noqa: E402


def calls(raw):
    internal = syscalls = 0
    for i in range(0, len(raw), 8):
        if raw[i] == 0x85:
            imm = struct.unpack_from('<i', raw, i + 4)[0]
            if raw[i + 1] >> 4 == 1 and imm != -1:
                internal += 1
            else:
                syscalls += 1
    return internal, syscalls


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('start')
    ap.add_argument('--sym', help='regex over mangled or demangled candidate symbols')
    ap.add_argument('--top', type=int, default=3)
    ap.add_argument('--slots', type=int, default=12, help='how many differing slot offsets to list')
    a = ap.parse_args()
    start = int(a.start, 0)
    w = next(x for x in original_windows() if x['start'] == start)
    cand = Cand(a.candidate)
    if a.sym:
        picks = [(s, n, nm) for s, n, nm in cand.funcs if re.search(a.sym, nm) or re.search(a.sym, demangle(nm))]
    else:
        picks = [(s, n, nm) for _, _, s, n, nm in best_candidates(w, cand, a.top)]
    otok = [x[2] for x in insns(w['raw'], start, ORIG_SECS)]
    ocalls = calls(w['raw'])
    rows = []
    for s, n, nm in picks:
        raw = cand.fn(s, n)
        norm = normalize(raw, s, cand.secs)
        ctok = [x[2] for x in insns(raw, s, cand.secs)]
        row = {'window': hex(start), 'window_bytes': w['bytes'], 'symbol': demangle(nm), 'cand_start': hex(s), 'cand_bytes': n,
               'normalized_equal': norm == w['norm'], 'raw_equal': raw == w['raw'],
               'ratio': round(difflib.SequenceMatcher(None, otok, ctok, autojunk=False).ratio(), 5),
               'calls_original': ocalls, 'calls_candidate': calls(raw)}
        if n == w['bytes']:
            diff = [i for i in range(0, n, 8) if norm[i:i + 8] != w['norm'][i:i + 8]]
            row['slots_diff'] = len(diff)
            row['first_diff_offsets'] = [hex(i) for i in diff[:a.slots]]
        rows.append(row)
    rows.sort(key=lambda r: (-r['normalized_equal'], r.get('slots_diff', 1 << 30), -r['ratio']))
    for row in rows[:a.top] if not a.sym else rows:
        print(json.dumps(row))


if __name__ == '__main__':
    main()
