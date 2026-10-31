#!/usr/bin/env python3
"""jdelta.py fn.bin: L3-aligned (jump offsets masked) pairs of jumps; prints, per pair with differing offsets,
orig src/target vs ours, and a histogram of (ours target - aligned-orig-target mapping) deltas. Experiment only."""
import sys, os, difflib, collections, re
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from bdis import decode
_a=sys.argv; sys.argv=[_a[0],_a[1],"0","8"]; import io; _so=sys.stdout; sys.stdout=io.StringIO()
import cls as C
sys.argv=_a; sys.stdout=_so
O = open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a90-cto-tcfweight/orig.bin'), 'rb').read(); c = open(sys.argv[1], 'rb').read()
oi = decode(O); ci = decode(c)
def tk(raw, ins, lv): return [C.mask(raw[d['off']:d['off'] + d['n']], lv) for d in ins]
sm = difflib.SequenceMatcher(None, tk(O, oi, 3), tk(c, ci, 3), autojunk=False)
o2c = {}
for a, b, n in sm.get_matching_blocks():
    for k in range(n): o2c[oi[a + k]['off']] = ci[b + k]['off']
H = collections.Counter(); bad = []
for a, b, n in sm.get_matching_blocks():
    for k in range(n):
        od, cd = oi[a + k], ci[b + k]
        m = re.search(r'([+-]\d+)$', od['txt'])
        if not m or not (od['txt'].startswith('j')): continue
        mc = re.search(r'([+-]\d+)$', cd['txt'])
        ot = od['off'] + 8 + 8 * int(m.group(1)); ct = cd['off'] + 8 + 8 * int(mc.group(1))
        if ot == od['off'] + 8 and False: continue
        exp = o2c.get(ot)
        if int(m.group(1)) != int(mc.group(1)):
            d = (int(mc.group(1)) - int(m.group(1)))
            H[d] += 1; bad.append((od['off'], ot, cd['off'], ct, d, exp == ct if exp is not None else None))
print('jump pairs with offset diff:', len(bad))
print('delta histogram (insns):', sorted(H.items(), key=lambda x: -x[1])[:15])
lim = int(sys.argv[2]) if len(sys.argv) > 2 else 40
for x in bad[:lim]: print('orig %05x->%05x  ours %05x->%05x  d=%+d  target-aligned=%s' % x)
