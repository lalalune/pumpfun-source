#!/usr/bin/env python3
"""sbs.py <m.dis> lo hi [--main m2.dis]: side-by-side frame-masked diff of orig region [lo,hi) vs candidate."""
import sys,re,difflib
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/tools')
from absratio import norm
O=[l.split(None,1) for l in open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/orig.rel') if len(l.split(None,1))>1]
C=[l.split(None,1) for l in open(sys.argv[1]) if len(l.split(None,1))>1]
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
a=[norm(x[1],False) for x in O]; b=[norm(x[1],False) for x in C]
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    oi=[k for k in range(i1,i2) if lo<=int(O[k][0],16)<hi]
    if not oi and not (tag=='insert' and i1<len(O) and lo<=int(O[min(i1,len(O)-1)][0],16)<hi): continue
    if tag=='equal': print(f'  = {len(oi)} equal ({O[i1][0]}..)'); continue
    n=max(i2-i1,j2-j1)
    for k in range(n):
        l=f'{O[i1+k][0]} {O[i1+k][1].strip()[:44]}' if i1+k<i2 else ''
        r=f'{C[j1+k][0]} {C[j1+k][1].strip()[:44]}' if j1+k<j2 else ''
        print(f'{tag[0]} {l:52s} | {r}')
