#!/usr/bin/env python3
"""Plan size-compensating combos from single-gene screen results on a base set.
  plan.py <baseset> [target_bytes=27400] [max_genes=3] [min_ratio]"""
import json, sys, itertools
from pathlib import Path
sys.path.insert(0, str(Path.home() / '.cache/pumpfun-reconstruction/lanes/w12a14-cto-hillclimb/hc'))
from hc12 import done_ids, apply, load_genes, BASEFILE, vid_of
G = load_genes(str(Path.home() / '.cache/pumpfun-reconstruction/lanes/w12a14-cto-hillclimb/hc/genes12.py'))
bs = [x for x in sys.argv[1].split(',') if x]
target = int(sys.argv[2]) if len(sys.argv) > 2 else 27400
maxg = int(sys.argv[3]) if len(sys.argv) > 3 else 3
minr = float(sys.argv[4]) if len(sys.argv) > 4 else 0.43919
d = done_ids()
base = BASEFILE.read_text()
bt = apply(base, G, bs)
br = d.get(vid_of(bt))
if not br or br.get('status') != 'built':
    print('base not built'); sys.exit(1)
print('base', br['bytes'], br['ratio'])
singles = {}
for g in G:
    if g in bs: continue
    try:
        t = apply(bt, G, [g])
    except Exception:
        continue
    r = d.get(vid_of(t))
    if r and r.get('status') == 'built' and not r.get('losses'):
        singles[g] = (r['bytes'] - br['bytes'], r['ratio'] - br['ratio'])
print(len(singles), 'singles measured')
for g, (db, dr) in sorted(singles.items(), key=lambda kv: -kv[1][1]):
    print(f'  {g:28s} {db:+5d} {dr:+.5f}')
need = target - br['bytes']
cands = []
for k in range(1, maxg + 1):
    for combo in itertools.combinations(singles, k):
        db = sum(singles[g][0] for g in combo); dr = sum(singles[g][1] for g in combo)
        if db == need and br['ratio'] + dr > minr:
            try:
                t = apply(bt, G, list(combo))
            except Exception:
                continue
            if vid_of(t) in d: continue
            cands.append((dr, combo))
cands.sort(reverse=True)
print('need', need, 'combos', len(cands))
for dr, combo in cands[:40]:
    print(f'  est {br["ratio"]+dr:.5f}  {",".join(bs+list(combo))}')
