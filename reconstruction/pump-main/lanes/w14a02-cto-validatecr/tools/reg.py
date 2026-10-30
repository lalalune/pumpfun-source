#!/usr/bin/env python3
"""reg.py <m.o>...: per 0x800-byte original region, count of orig instructions matched (regs/frame masked alignment)."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from abs import n1,n2
o=orig_dis(); W=int(os.environ.get("W","0x800"),16)
rows=[]
for p in sys.argv[1:]:
    c=cand_dis(p)
    for f in (n2,n1):
        sm=difflib.SequenceMatcher(None,[f(t) for _,t in o],[f(t) for _,t in c],autojunk=False)
        cnt=[0]*(o[-1][0]//W+1)
        for a,b,n in sm.get_matching_blocks():
            for k in range(n): cnt[o[a+k][0]//W]+=1
        rows.append((p.split('/')[-2]+('.rm' if f is n2 else '.fm'),cnt))
print('%-10s'%'reg',' '.join('%5x'%(i*W//0x100) for i in range(len(rows[0][1]))))
for n,c in rows: print('%-10s'%n,' '.join('%5d'%x for x in c),sum(c))
