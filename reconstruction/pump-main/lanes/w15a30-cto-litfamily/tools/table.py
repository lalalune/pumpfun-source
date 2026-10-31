#!/usr/bin/env python3
"""table.py: per-literal family table from res-<sha>.jsonl (litfamily screen). Experiment only."""
import json,sys,collections
R=sys.argv[1]
rows=[json.loads(l) for l in open(R)]
by={}
for r in rows: by[r['name']]=r   # last wins
main=by.get('M_main',{}).get('M',2249)
fam=collections.OrderedDict()
for n,r in by.items():
    if n=='M_main': continue
    k=r.get('genes','').split(':')[0] if ';' not in r.get('genes','') else 'combo'
    fam.setdefault(k,[]).append(r)
print('| literal | variants | eq main | at 27,400 B | best M (dM) | best variant | bytes of best |')
print('| --- | ---: | ---: | ---: | ---: | --- | ---: |')
for k,v in fam.items():
    ok=[r for r in v if 'M' in r]
    eq=sum(1 for r in ok if r.get('eq_main'))
    pin=sum(1 for r in ok if r.get('bytes')==27400)
    b=max(ok,key=lambda r:(r['M'],-abs(r['bytes']-27400))) if ok else None
    print(f"| {k} | {len(v)} | {eq} | {pin} | {b['M']} ({b['M']-main:+d}) | `{b['genes']}` | {b['bytes']} |" if b else f"| {k} | {len(v)} | - | - | - | - | - |")
