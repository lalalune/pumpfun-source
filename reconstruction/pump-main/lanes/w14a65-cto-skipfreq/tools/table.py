#!/usr/bin/env python3
"""table.py <jsonl>..: per head-weight summary of pair.py rows (markdown).
moved0 = reorder.py chain order equal to main; spill = sweep-gate flag in no callee-saved reg over the wallet
(flag known only for rows with F >= FMIN, so 'm0+spill' counts are lower bounds when F < FMIN)."""
import sys,json,collections
G=collections.defaultdict(list)
for f in sys.argv[1:]:
    for l in open(f):
        r=json.loads(l)
        if 'F' not in r: continue
        k=('%s %s'%(r['e'][0][0][:24],r['e'][0][2])) if r['k']=='pair' else r['k']
        G[k].append(r)
print('| head | rows | moved 0 | moved 0 + flag spilled | max F | max F, moved 0 | max F, moved 0 + spilled | max Fw, spilled | max ratio (bytes) |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |')
for k,R in G.items():
    m0=[r for r in R if r['moved']==0]; ms=[r for r in m0 if r.get('flag')=='spill']; sp=[r for r in R if r.get('flag')=='spill']
    mx=max(R,key=lambda r:r['ratio'])
    f=lambda L:('%.5f'%max(r['F'] for r in L)) if L else '-'
    print('| %s | %d | %d | %d | %s | %s | %s | %s | %.5f (%d) |'%(k,len(R),len(m0),len(ms),f(R),f(m0),f(ms),max([r['Fw'] for r in sp] or [0]) or '-',mx['ratio'],mx['bytes']))
