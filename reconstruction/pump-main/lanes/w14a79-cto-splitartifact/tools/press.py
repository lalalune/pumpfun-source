#!/usr/bin/env python3
"""press.py fn.bin lo hi: register pressure along L2-aligned pairs of orig [lo,hi): live-out register count orig vs
ours at each Rc-increment (ldxdw rA,[rB+0]; add64 rA,1) pair, plus the window totals. Experiment only."""
import sys, os, difflib
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import artifacts as A
import cls as C
f, lo, hi = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
O = open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a79-cto-splitartifact/orig.bin'), 'rb').read(); c = open(f, 'rb').read()
oi, ol = A.liveness(O); ci, cl = A.liveness(c)
def tk(raw, ins): return [C.mask(raw[d['off']:d['off'] + d['n']], 2) for d in ins]
sm = difflib.SequenceMatcher(None, tk(O, oi), tk(c, ci), autojunk=False)
so = sc = n = 0
for a, b, m in sm.get_matching_blocks():
    for k in range(m):
        od, cd = oi[a + k], ci[b + k]
        if not (lo <= od['off'] < hi): continue
        lo_, lc = ol[a + k] - {10}, cl[b + k] - {10}; so += len(lo_); sc += len(lc); n += 1
        if od['op'] == 0x07 and od['imm'] == 1 and a + k > 0 and oi[a + k - 1]['o'] == 0 and oi[a + k - 1]['op'] == 0x79:
            print('%04x|%04x  orig %d %-22s ours %d %s' % (od['off'], cd['off'], len(lo_), ','.join('r%d' % r for r in sorted(lo_)), len(lc), ','.join('r%d' % r for r in sorted(lc))))
print('aligned %d  mean live orig %.2f ours %.2f' % (n, so / max(n, 1), sc / max(n, 1)))
