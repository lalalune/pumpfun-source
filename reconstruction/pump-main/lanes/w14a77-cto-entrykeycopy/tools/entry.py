#!/usr/bin/env python3
"""entry.py <m.o|so> [--show]: register-masked (rm) and frame-masked (fm) local alignment of orig 0x0-0x800 against
cand prefix [0,0xa00); also global rm per-0x200 chunk counts for 0x0-0x800 and whole-window totals."""
import sys,os,difflib,json
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from abs import n1,n2
o=orig_dis(); OE=[(a,t) for a,t in o if a<0x800]
def run(p,show=False):
    c=cand_dis(p); CE=[(a,t) for a,t in c if a<0xa00]
    r={'name':p.split('/')[-2],'bytes':sum(16 if t.startswith('lddw') else 8 for _,t in c)}
    for nm,f in (('L_rm',n2),('L_fm',n1),('L_ex',lambda s:s)):
        sm=difflib.SequenceMatcher(None,[f(t) for _,t in OE],[f(t) for _,t in CE],autojunk=False)
        r[nm]=sum(n for _,_,n in sm.get_matching_blocks())
        if nm=='L_rm': mb=sm.get_matching_blocks()
    sm=difflib.SequenceMatcher(None,[n2(t) for _,t in o],[n2(t) for _,t in c],autojunk=False)
    cnt=[0]*(o[-1][0]//0x200+1)
    for a,b,n in sm.get_matching_blocks():
        for k in range(n): cnt[o[a+k][0]//0x200]+=1
    r['G_rm0800']=sum(cnt[:4]); r['G_rmT']=sum(cnt); r['n']=(len(OE),len(CE))
    if show:
        m={}
        for a,b,n in mb:
            for k in range(n): m[a+k]=b+k
        for i,(a,t) in enumerate(OE):
            j=m.get(i); print('%5x %-40s %s'%(a,t,('%5x %s'%CE[j] if j is not None else '   --')))
    return r
for p in [x for x in sys.argv[1:] if not x.startswith('--')]:
    print(json.dumps(run(p,'--show' in sys.argv)))
