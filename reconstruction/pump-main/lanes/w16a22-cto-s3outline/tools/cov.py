#!/usr/bin/env python3
"""cov.py <ra.txt> <slot> <minvreg>: final physreg of every vreg (id >= minvreg) whose assigned segments cover <slot>."""
import sys,re
f,slot,mv=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
fin={}
pat=re.compile(r'\[(\d+)[Berd],(\d+)[Berd]:')
for l in open(f):
    if l.startswith('assigning %'):
        m=re.match(r'assigning %(\d+) to (\$r\d+)',l); n=int(m.group(1))
        if n<mv: continue
        for a,b in pat.findall(l):
            if int(a)<=slot<int(b): fin[n]=m.group(2); break
        else: fin.pop(n,None)
    elif l.startswith('unassigning %'):
        m=re.match(r'unassigning %(\d+)',l); fin.pop(int(m.group(1)),None)
print(sorted(fin.items()))
