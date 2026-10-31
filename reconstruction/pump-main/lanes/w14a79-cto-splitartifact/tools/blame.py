#!/usr/bin/env python3
"""blame.py fn.bin [lo hi]: attribute each register-only miss (L2-equal, L1-different aligned pair) in orig [lo,hi)
to the occupant of the orig's register in OURS at that point: for every differing register field (orig ro, ours rc),
if ro is live (occupied) in ours across the aligned instruction, the miss is blamed on ours' occupant of ro (its def
instruction, traced back through machine-code liveness); otherwise 'free' (pure assignment choice).
Also reports the symmetric blame (rc occupied in the original). Experiment only."""
import sys, os, difflib, collections
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import artifacts as A
from artifacts import liveness
import cls as C
f = sys.argv[1]; lo = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x2800; hi = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x4000
O = open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a79-cto-splitartifact/orig.bin'), 'rb').read(); c = open(f, 'rb').read()
oi, olo = liveness(O); osu = A.LAST_SUCC; ci, clo = liveness(c); csu = A.LAST_SUCC
def tk(raw, ins, lv): return [C.mask(raw[d['off']:d['off'] + d['n']], lv) for d in ins]
sm = difflib.SequenceMatcher(None, tk(O, oi, 2), tk(c, ci, 2), autojunk=False)
o1 = tk(O, oi, 1); c1 = tk(c, ci, 1)
def occupant(ins, lout, k, r, succ=None):
    # live-through: r live before and after k and not touched by k
    lin = (lout[k] - ins[k]['writes']) | ins[k]['reads']
    if r not in lin or r in ins[k]['writes'] or r in ins[k]['reads']:
        if not (r in lout[k - 1] if k else False): return None
    ds = A.reaching(ins, succ, k, r)
    if not ds: return None
    d = dict(ins[ds[0]]); d['txt'] = ' / '.join('%04x %s' % (ins[q]['off'], ins[q]['txt']) for q in ds[:3]) + (' +%d' % (len(ds) - 3) if len(ds) > 3 else ''); d['off'] = -1 if len(ds) > 1 else ins[ds[0]]['off']
    return d
blame = collections.Counter(); blame2 = collections.Counter(); n = 0; free = 0; ex = collections.defaultdict(list)
for a, b, m in sm.get_matching_blocks():
    for k in range(m):
        od, cd = oi[a + k], ci[b + k]
        if not (lo <= od['off'] < hi) or o1[a + k] == c1[b + k]: continue
        n += 1; hit = False
        for fld in ('dst', 'src'):
            ro, rc = od[fld], cd[fld]
            if ro == rc: continue
            occ = occupant(ci, clo, b + k, ro, csu)
            if occ is not None and occ['off'] != cd['off']:
                key = 'ours r%d <- %s' % (ro, occ['txt']); blame[key] += 1; ex[key].append(od['off']); hit = True; break
            occ2 = occupant(oi, olo, a + k, rc, osu)
            if occ2 is not None and occ2['off'] != od['off']:
                key = 'orig r%d <- %s' % (rc, occ2['txt']); blame2[key] += 1; ex[key].append(od['off']); hit = True; break
        if not hit: free += 1
print('register-only misses %d in orig [%#x,%#x): blocked-by-ours-occupant %d, blocked-by-orig-occupant %d, free %d'
      % (n, lo, hi, sum(blame.values()), sum(blame2.values()), free))
for k, v in blame.most_common(25): print('%4d  %s   e.g. orig %s' % (v, k, ' '.join('%04x' % x for x in ex[k][:6])))
print('--')
for k, v in blame2.most_common(15): print('%4d  %s   e.g. orig %s' % (v, k, ' '.join('%04x' % x for x in ex[k][:6])))
