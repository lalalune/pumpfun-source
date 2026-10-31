#!/usr/bin/env python3
"""regpairs.py <so> lo hi : within [lo,hi) align orig/cand with regs+frame masked, then count (orig reg -> cand reg)
pairs for dst and src fields of aligned instructions whose registers differ. Shows the dominant register permutation."""
import sys, difflib, collections
from pathlib import Path
import importlib.util
p = Path(__file__).resolve().parent / 'splice.py'
spec = importlib.util.spec_from_file_location('splice', p); sys.argv_s = sys.argv; sys.argv = ['x']
sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp); sys.argv = sys.argv_s
so, lo, hi = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
o, k, on, cn = sp.load(so)
a = [t for off, t in o if lo <= off < hi]; b = [t for off, t in k if lo <= off < hi]
sm = difflib.SequenceMatcher(None, [sp.mask(x, 2) for x in a], [sp.mask(x, 2) for x in b], autojunk=False)
c = collections.Counter(); n = 0
for blk in sm.get_matching_blocks():
    for i in range(blk.size):
        x, y = a[blk.a + i], b[blk.b + i]
        if x[1] != y[1]:
            n += 1
            if x[1] & 15 != y[1] & 15: c[('r%d' % (x[1] & 15), 'r%d' % (y[1] & 15))] += 1
            if x[1] >> 4 != y[1] >> 4: c[('r%d' % (x[1] >> 4), 'r%d' % (y[1] >> 4))] += 1
print('aligned insns with register differences:', n)
for (p_, q), v in c.most_common(12): print(f'  orig {p_} -> ours {q}: {v}')
