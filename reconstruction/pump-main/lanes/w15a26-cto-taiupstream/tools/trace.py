#!/usr/bin/env python3
"""trace.py ra.log root...: follow a vreg family (root + split products) through the RAPRIO log: dequeues, assignments, evictions."""
import sys,re
log=sys.argv[1]; fam=set(sys.argv[2:]); L=open(log).read().split('\n')
q={}
for l in L:
    p=l.split()
    if p and p[0]=='Q': q[p[1]]=' '.join(p[2:])
for i,l in enumerate(L,1):
    p=l.split()
    if not p: continue
    if p[0]=='R' and p[1] in fam and 'new:' in l:
        for v in l.split('new:')[1].split(): fam.add(v)
    hit = (p[0] in 'DR' and (p[1] in fam if p[0]=='R' else p[2] in fam)) or (p[0]=='E' and (p[1] in fam)) or (p[0]=='S' and p[1] in fam) or (p[0]=='E' and p[-1] in fam)
    if hit:
        v=p[1] if p[0]!='D' else p[2]
        extra=f'   [{q.get(v,"")}]' if p[0]=='D' else ''
        if p[0]=='E' and p[1] in fam: extra=f'   evictor [{q.get(p[-1],"")}]'
        print(i,l+extra)
