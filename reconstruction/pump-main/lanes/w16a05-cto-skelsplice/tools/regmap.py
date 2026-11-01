#!/usr/bin/env python3
"""regmap.py <build> <lo> <hi> [--ref orig|main|<build>]: register correspondence (orig reg -> cand reg counts) over
skeleton-matched instructions in an orig range; shows whether a region's naming loss is a consistent permutation."""
import sys,os,difflib
from collections import Counter,defaultdict
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled
from regprof import path
O=oracle.orig_window(); ot,oo=xled.toks(O)
p=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
C=xled.load(path(p)); ct,co=xled.toks(C)
m=defaultdict(Counter)
for bl in difflib.SequenceMatcher(None,xled.fmask(ot),xled.fmask(ct),autojunk=False).get_matching_blocks():
    for k in range(bl.size):
        i=bl.a+k; j=bl.b+k
        if not (lo<=oo[i]<hi): continue
        x=ot[i]; y=ct[j]
        for sh in (0,4):
            a=(x[1]>>sh)&15; b=(y[1]>>sh)&15
            if a==10 and b==10: continue
            m[a][b]+=1
for a in sorted(m):
    tot=sum(m[a].values()); top=', '.join(f'r{b}:{n}' for b,n in m[a].most_common(4))
    print(f'orig r{a:<2d} n={tot:4d} -> {top}')
