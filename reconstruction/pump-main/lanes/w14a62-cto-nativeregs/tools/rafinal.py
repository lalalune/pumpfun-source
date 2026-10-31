#!/usr/bin/env python3
"""rafinal.py <greedy.log> <slot> [slot2]: final greedy assignments whose live ranges cover the slot(s)"""
import sys,re
log=open(sys.argv[1]).read().split('\n'); pts=[int(x) for x in sys.argv[2:]]
cur={}; rng={}
for l in log:
    m=re.match(r'assigning (%\d+) to (\$r\d+): \S+ (.*)',l)
    if m: cur[m.group(1)]=m.group(2); rng[m.group(1)]=m.group(3); continue
    m=re.match(r'unassigning (%\d+) from',l)
    if m: cur.pop(m.group(1),None)
def cov(r,p):
    for a,b in re.findall(r'\[(\d+)[a-zA-Z],(\d+)[a-zA-Z]:',r):
        if int(a)<=p<int(b): return True
    return False
for p in pts:
    print('slot',p)
    for v,reg in sorted(cur.items(),key=lambda x:x[1]):
        if cov(rng[v],p): print('  ',reg,v,len(re.findall(r'\[',rng[v])),'segs')
