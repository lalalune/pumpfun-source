#!/usr/bin/env python3
"""drift.py <so> [--lvl 2] [--step 0x400] : size-drift map. Globally aligns orig/cand tokens at mask level lvl and
reports, per orig chunk, the median (cand offset - orig offset) of matched instructions. A change of drift between
chunks = bytes ours adds (+) or lacks (-) there; jump offsets that cross that chunk and every positional slot after it
are off by that amount."""
import sys, difflib, statistics
from pathlib import Path
import importlib.util
p = Path(__file__).resolve().parent / 'splice.py'
spec = importlib.util.spec_from_file_location('splice', p); sv = sys.argv; sys.argv = ['x']
sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp); sys.argv = sv
a = sys.argv[1:]; so = a[0]
lvl = int(a[a.index('--lvl')+1]) if '--lvl' in a else 2
st = int(a[a.index('--step')+1], 0) if '--step' in a else 0x400
o, k, on, cn = sp.load(so)
sm = difflib.SequenceMatcher(None, [sp.mask(x, lvl) for _, x in o], [sp.mask(x, lvl) for _, x in k], autojunk=False)
d = {}
for b in sm.get_matching_blocks():
    for i in range(b.size): d[o[b.a+i][0]] = k[b.b+i][0] - o[b.a+i][0]
prev = None
for lo in range(0, len(on), st):
    v = [d[x] for x in d if lo <= x < lo+st]
    if not v: print(f'{lo:#06x}  (no matches)'); continue
    m = int(statistics.median(v)); ch = '' if prev is None else f'{m-prev:+d}'
    print(f'{lo:#06x}  matched {len(v):3d}  drift median {m:+5d}  min {min(v):+5d} max {max(v):+5d}  step {ch}')
    prev = m
