#!/usr/bin/env python3
"""Classify every unmatched original window against the candidate.

Categories: coord (only Source line/filename-length immediates differ), near<=3, frame,
equal-len (equal length, other diffs), body (no equal-length candidate).
Writes JSON (default base/current/triage.json) and prints a summary.
"""
import argparse, json, sys
from collections import Counter, defaultdict
from pathlib import Path

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
from score import sections, body, normalize, original_windows, score, BASE, candidate_functions  # noqa
from coords import sites, non_coordinate_slots, ORIG, OS  # noqa
from win import demangle  # noqa

FRAME_LOADS = {0x61, 0x69, 0x71, 0x79}   # ldx*: r10 is the source register
FRAME_STORES = {0x62, 0x63, 0x6a, 0x6b, 0x72, 0x73, 0x7a, 0x7b}  # stx*: r10 is the destination
FRAME_WRITES = {0x07, 0xb7, 0xbf}        # add64/mov64 immediates and mov64 register


def frame_slot(raw, i):
    """True when the instruction at i uses r10 as its frame operand."""
    op, regs = raw[i], raw[i + 1]
    if op in FRAME_LOADS:
        return regs >> 4 == 10
    if op in FRAME_STORES:
        return regs & 0xf == 10
    return op in FRAME_WRITES and regs & 0xf == 10


def write_report(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cand', type=Path, default=BASE / 'current/unstripped.so')
    ap.add_argument('--json', type=Path, default=BASE / 'current/triage.json')
    a = ap.parse_args()
    blob = a.cand.read_bytes(); cs = sections(blob)
    cur = score(a.cand)
    bylen = defaultdict(list)
    for s, n, nm in candidate_functions(a.cand):
        bylen[n].append((s, nm))
    cache = {}; rows = []
    for w in original_windows():
        if cur[w['start']]['normalized']:
            continue
        osites = sites(ORIG, OS, w['start'], w['raw'])
        on = normalize(w['raw'], w['start'], OS)
        best = None
        for (s, nm) in bylen.get(w['bytes'], []):
            if s not in cache:
                cache[s] = normalize(body(blob, cs, s, w['bytes']), s, cs)
            cn = cache[s]
            diff = [i for i in range(0, len(on), 8) if on[i:i + 8] != cn[i:i + 8]]
            noncoord = non_coordinate_slots(on, cn, osites)
            key = (len(noncoord), len(diff))
            if best is None or key < best[0]:
                best = (key, s, nm, diff, noncoord)
        if best is None:
            cat = 'body'
        else:
            nc = best[4]
            if not nc:
                cat = 'coord'
            elif len(nc) <= 3:
                cat = 'near<=3'
            else:
                cat = 'frame' if all(frame_slot(on, d) for d in nc) else 'equal-len'
        rows.append({'start': hex(w['start']), 'bytes': w['bytes'], 'category': cat, 'has_source_sites': bool(osites),
                     'original_sites': [{'path': s['path'], 'line': s['line']} for s in osites],
                     'nearest': None if best is None else {'addr': hex(best[1]), 'symbol': demangle(best[2]), 'diff_slots': len(best[3]), 'noncoord_slots': len(best[4])}})
    write_report(a.json, rows)
    c = Counter(r['category'] for r in rows); b = Counter()
    for r in rows:
        b[r['category']] += r['bytes']
    for k in ['coord', 'near<=3', 'frame', 'equal-len', 'body']:
        print(f"{k:10s} {c[k]:4d} windows {b[k]:8d} B")
    print('total', len(rows))


if __name__ == '__main__':
    main()
