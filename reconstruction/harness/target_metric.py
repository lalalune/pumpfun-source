#!/usr/bin/env python3
"""Measure how close a candidate build is to one original window.

  target_metric.py <unstripped.so> <orig_start> [<orig_start> ...] [--sym REGEX] [--top N] [--slots N]

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
from instruction_stream import instruction_offsets


def calls(raw):
    internal = syscalls = 0
    for i in instruction_offsets(raw):
        if raw[i] == 0x85:
            imm = struct.unpack_from('<i', raw, i + 4)[0]
            if raw[i + 1] >> 4 == 1 and imm != -1:
                internal += 1
            else:
                syscalls += 1
    return internal, syscalls


def measure_window(w, cand, pattern=None, top=3, slots=12):
    """Measure one window while sharing the loaded candidate across a batch."""
    start = w['start']
    if pattern:
        picks = [(s, n, nm) for s, n, nm in cand.funcs if pattern.search(nm) or pattern.search(demangle(nm))]
    else:
        picks = [(s, n, nm) for _, _, s, n, nm in best_candidates(w, cand, top)]
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
            row['first_diff_offsets'] = [hex(i) for i in diff[:slots]]
        rows.append(row)
    rows.sort(key=lambda r: (-r['normalized_equal'], r.get('slots_diff', 1 << 30), -r['ratio']))
    return rows[:top] if pattern is None else rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('start', nargs='+', type=lambda value: int(value, 0), help='one or more original window addresses')
    ap.add_argument('--sym', help='regex over mangled or demangled candidate symbols')
    ap.add_argument('--top', type=int, default=3)
    ap.add_argument('--slots', type=int, default=12)
    ap.add_argument('--json', type=Path, help='also save all rows as one JSON array')
    a = ap.parse_args(argv)
    if a.top <= 0 or a.slots < 0:
        ap.error('--top must be positive and --slots must be nonnegative')
    try:
        pattern = re.compile(a.sym) if a.sym is not None else None
    except re.error as error:
        ap.error(f'invalid symbol regex: {error}')
    starts = list(dict.fromkeys(a.start))
    windows = {w['start']: w for w in original_windows()}
    missing = [hex(start) for start in starts if start not in windows]
    if missing:
        ap.error('unknown original windows: ' + ', '.join(missing))
    cand = Cand(a.candidate)
    rows = [row for start in starts for row in measure_window(windows[start], cand, pattern, a.top, a.slots)]
    if a.json:
        try:
            a.json.parent.mkdir(parents=True, exist_ok=True)
            with a.json.open('x', encoding='utf-8') as stream:
                stream.write(json.dumps(rows, indent=2) + '\n')
        except OSError as error:
            ap.error(f'cannot create diagnostic report: {error}')
    for row in rows:
        print(json.dumps(row))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
