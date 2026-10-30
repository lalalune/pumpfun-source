#!/usr/bin/env python3
"""regcov.py <m.dis>...: per 0x800 orig region, fraction of orig insts matched (frame-masked difflib)."""
import sys,re,difflib
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a18-cto-feephi/tools')
from absratio import norm
O=[l.split(None,1)[1] for l in open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a18-cto-feephi/orig.rel') if len(l.split(None,1))>1]
a=[norm(x,False) for x in O]; R=0x800//8; nreg=(len(a)+R-1)//R
rows=[]
for f in sys.argv[1:]:
    C=[l.split(None,1)[1] for l in open(f) if len(l.split(None,1))>1]; b=[norm(x,False) for x in C]
    m=[0]*len(a)
    for bl in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        for i in range(bl.a,bl.a+bl.size): m[i]=1
    rows.append([sum(m[i*R:(i+1)*R])/len(m[i*R:(i+1)*R]) for i in range(nreg)])
print('region '+' '.join(f'{x[-14:]:>14}' for x in sys.argv[1:]))
for i in range(nreg): print(f'{i*0x800:#06x} '+' '.join(f'{r[i]:14.3f}' for r in rows))
