#!/usr/bin/env python3
"""bincov.py A.dis B.dis [bin]: per orig bin, matched (frame-masked) counts for A and B; prints bins where they differ."""
import sys,difflib
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/tools')
from absratio import norm
O=[l.split(None,1) for l in open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a45-cto-lv3frame/orig.rel') if len(l.split(None,1))>1]
a=[norm(x[1],False) for x in O]; B=int(sys.argv[3],16) if len(sys.argv)>3 else 0x100
def cov(f):
    C=[l.split(None,1)[1] for l in open(f) if len(l.split(None,1))>1]; b=[norm(x,False) for x in C]
    m=[0]*len(O)
    for bl in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        for k in range(bl.size): m[bl.a+k]=1
    return m
ma,mb=cov(sys.argv[1]),cov(sys.argv[2]); bins={}
for k,x in enumerate(O):
    h=int(x[0],16)//B*B; s=bins.setdefault(h,[0,0,0]); s[0]+=1; s[1]+=ma[k]; s[2]+=mb[k]
tot=0
for h,(n,x,y) in sorted(bins.items()):
    if x!=y: print(f'{h:#06x} n={n:3d} A={x:3d} B={y:3d} d={y-x:+d}'); tot+=y-x
print('total',tot)
