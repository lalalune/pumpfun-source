#!/usr/bin/env python3
"""span.py <m.o>...: per original 0x400 region, candidate byte span mapped via regs/frame-masked alignment (cand-orig delta)."""
import sys,os,difflib,bisect
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from abs import n2
o=orig_dis(); W=0x400
for p in sys.argv[1:]:
    c=cand_dis(p)
    sm=difflib.SequenceMatcher(None,[n2(t) for _,t in o],[n2(t) for _,t in c],autojunk=False)
    pairs=[(o[a+k][0],c[b+k][0]) for a,b,n in sm.get_matching_blocks() for k in range(n)]
    oo=[x for x,_ in pairs]
    def mp(x):
        i=bisect.bisect_left(oo,x); i=min(i,len(pairs)-1); return pairs[i][1]-(pairs[i][0]-x)
    row=[]
    for r in range(0,o[-1][0]+8,W):
        e=min(r+W,o[-1][0]+8); row.append((mp(e)-mp(r))-(e-r))
    print('%-8s'%p.split('/')[-2],' '.join('%+5d'%x for x in row), sum(row))
print('%-8s'%'reg',' '.join('%5x'%(r//0x100) for r in range(0,o[-1][0]+8,W)))
