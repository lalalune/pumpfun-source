#!/usr/bin/env python3
"""reg8.py <m.o|so>...: per-0x800 orig region exact-match / fm / rm counts (global alignment)."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from slots import orig_dis,cand_dis
from abs import n1,n2
o=orig_dis(); W=0x800
print('%-10s'%'name','  '.join('%5x'%(k*W) for k in range(o[-1][0]//W+1)))
for p in sys.argv[1:]:
    c=cand_dis(p); out=[]
    for f in (lambda t:t,n1,n2):
        sm=difflib.SequenceMatcher(None,[f(t) for _,t in o],[f(t) for _,t in c],autojunk=False)
        cnt=[0]*(o[-1][0]//W+1)
        for a,b,n in sm.get_matching_blocks():
            for k in range(n): cnt[o[a+k][0]//W]+=1
        out.append(cnt)
    nm=p.split('/')[-2]
    for lab,cnt in zip(('ex','fm','rm'),out): print('%-10s'%(nm[:7]+':'+lab),' '.join('%5d'%x for x in cnt),'=',sum(cnt))
