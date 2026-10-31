#!/usr/bin/env python3
"""regmiss.py fn.bin [lo hi]: register-only misses (L2-aligned pairs equal at L2 but not at L1) in orig [lo,hi),
grouped by (orig reg -> ours reg) for the dst and src fields. Experiment only."""
import sys, os, difflib, collections
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
from bdis import decode
import cls as C
f = sys.argv[1]; lo = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x2800; hi = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x4000
O = open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a79-cto-splitartifact/orig.bin'), 'rb').read(); c = open(f, 'rb').read()
oi = decode(O); ci = decode(c)
def tk(raw, ins, lv): return [C.mask(raw[d['off']:d['off'] + d['n']], lv) for d in ins]
sm = difflib.SequenceMatcher(None, tk(O, oi, 2), tk(c, ci, 2), autojunk=False)
o1 = tk(O, oi, 1); c1 = tk(c, ci, 1)
pairs = []; tot = 0
for a, b, n in sm.get_matching_blocks():
    for k in range(n):
        od, cd = oi[a + k], ci[b + k]
        if not (lo <= od['off'] < hi): continue
        tot += 1
        if o1[a + k] != c1[b + k]: pairs.append((od, cd))
print('L2-matched %d, register-only misses %d in orig [%#x,%#x)' % (tot, len(pairs), lo, hi))
g = collections.Counter()
for od, cd in pairs:
    for fld in ('dst', 'src'):
        if od[fld] != cd[fld]: g[(fld, od[fld], cd[fld])] += 1
by = collections.Counter()
for (fld, ro, rc), n in g.items(): by[(ro, rc)] += n
print('reg pair (orig->ours): count'); print(' '.join('r%d->r%d:%d' % (k[0], k[1], n) for k, n in by.most_common(30)))
if '--list' in sys.argv:
    for od, cd in pairs: print('%04x %-32s | %04x %s' % (od['off'], od['txt'], cd['off'], cd['txt']))
