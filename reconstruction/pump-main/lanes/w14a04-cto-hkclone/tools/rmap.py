#!/usr/bin/env python3
"""rmap.py <m.o> lo hi: over rm-aligned instructions in orig [lo,hi), count orig-reg -> cand-reg pairs, and list fm mismatches."""
import sys,os,re,difflib,collections
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from abs import n1,n2
p=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16); verbose=len(sys.argv)>4
o=orig_dis(); c=cand_dis(p)
sm=difflib.SequenceMatcher(None,[n2(t) for _,t in o],[n2(t) for _,t in c],autojunk=False)
m=collections.Counter(); bad=0
for a,b,n in sm.get_matching_blocks():
    for k in range(n):
        oa,ot=o[a+k]; ca,ct=c[b+k]
        if not lo<=oa<hi: continue
        ro=re.findall(r'\br(\d)\b',ot); rc=re.findall(r'\br(\d)\b',ct)
        for x,y in zip(ro,rc): m[(x,y)]+=1
        if n1(ot)!=n1(ct):
            bad+=1
            if verbose: print('%5x %-40s | %5x %s'%(oa,ot,ca,ct))
tot=collections.Counter()
for (x,y),v in m.items(): tot[x]+=v
for x in sorted(tot): print('orig r'+x,' '.join('r%s:%d'%(y,v) for (xx,y),v in sorted(m.items(),key=lambda kv:-kv[1]) if xx==x))
print('fm-mismatched aligned',bad)
