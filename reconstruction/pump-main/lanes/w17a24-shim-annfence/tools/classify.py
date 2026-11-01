#!/usr/bin/env python3
"""classify.py <ann_singles> <pt_singles> [base_sig]: split changed ann cells by what passthrough does at the same IR point."""
import json,sys,collections
A={json.loads(l)['id']:json.loads(l) for l in open(sys.argv[1])}
P={json.loads(l)['id']:json.loads(l) for l in open(sys.argv[2])}
B=sys.argv[3] if len(sys.argv)>3 else '85d273bcd66a'
C=collections.defaultdict(list)
for pid,p in P.items():
    if 'sig' not in p: continue
    i=pid[3:]; a=A.get(i)
    if not a or 'sig' not in a: continue
    if a['sig']==B: cls='ann-neutral'
    elif p['sig']==B: cls='cgp-isel-only'
    elif p['sig']==a['sig']: cls='opt-level(=pt)'
    else: cls='both'
    C[cls].append((i,a['M'],a['bytes'],p['M'],p['bytes']))
for k,v in C.items():
    print(k,len(v), collections.Counter(x[0].split(':')[0]+':'+x[0].split(':')[1] for x in v))
    for x in sorted(v,key=lambda x:-x[1])[:12]: print('   ',x)
