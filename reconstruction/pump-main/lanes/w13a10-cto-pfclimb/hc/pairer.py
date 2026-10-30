#!/usr/bin/env python3
"""pairer.py <log> [--top N] [--dry]: from single-gene screen results on BASE (27400, ratio R0) find gene pairs/triples
whose byte deltas sum to 0 and whose ratio deltas sum > 0; queue the untried ones (best predicted first)."""
import json, sys, itertools, subprocess, os
MAINREV = os.environ.get('HC_MAIN', '4394685')
from pathlib import Path
H = Path(__file__).parent
R0 = float(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith('-') else 0.49071
log = sys.argv[1]
rs = {}
for l in open(H / 'results.jsonl'):
    r = json.loads(l)
    if r.get('status') != 'built' or r.get('losses'): continue
    if r.get('main') != MAIN if False else False: pass
    rs[r['label']] = r
single = {}
base = rs.get('BASE')
for lab, r in rs.items():
    ids = lab.split(',')
    if ids[0] != 'BASE' and r.get('main') == MAINREV and r['ratio'] > 0.40:
        single[lab] = (r['bytes'] - 27400, r['ratio'] - R0, r.get('pf'))
tried = set(rs)
qtext = (H / 'queue.txt').read_text() if (H / 'queue.txt').exists() else ''
queued = set(l.strip() for l in qtext.splitlines())
cands = []
G = [g for g in single if not (single[g][0] == 0 and single[g][1] <= 0)]
for k in (2, 3):
    for combo in itertools.combinations(G, k):
        gs = [x for g in combo for x in g.split(',')]
        if len(gs) != len(set(gs)): continue
        db = sum(single[g][0] for g in combo)
        if db != 0 or all(single[g][0] == 0 for g in combo): continue
        dr = sum(single[g][1] for g in combo)
        if dr <= 0: continue
        lab = ','.join(gs)
        if lab in tried or lab in queued: continue
        cands.append((dr, lab))
cands.sort(reverse=True)
top = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 10
for dr, lab in cands[:top]: print(round(dr, 5), lab)
if '--dry' not in sys.argv and cands:
    subprocess.run([sys.executable, str(H / 'qadd.py'), 'top'] + [lab for _, lab in cands[:top]])
