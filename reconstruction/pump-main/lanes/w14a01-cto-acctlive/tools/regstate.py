#!/usr/bin/env python3
"""regstate.py <ra.log> <vreg> <physreg>: intervals assigned to physreg at the moment %vreg enters its RS_Split round."""
import sys,re
L=open(sys.argv[1]).read().split('\n'); v='selectOrSplit GPR:%'+sys.argv[2]+' '; R='$'+sys.argv[3]
cur={}
i=0
while i<len(L):
    l=L[i]
    m=re.match(r'assigning (%\d+) to (\$r\d+): \S+ (.*)',l)
    if m: cur[m.group(1)]=(m.group(2),m.group(3))
    m=re.match(r'unassigning (%\d+) from',l)
    if m: cur.pop(m.group(1),None)
    if l.startswith(v) and i+3<len(L) and any(L[k].startswith('RS_Split') for k in range(i,i+4)):
        break
    i+=1
for k,(r,rng) in cur.items():
    if r==R:
        segs=re.findall(r'\[(\d+)[rBde],(\d+)[rBde]',rng)
        print(k, len(segs), segs[0][0] if segs else '', segs[-1][1] if segs else '', rng[:150])
