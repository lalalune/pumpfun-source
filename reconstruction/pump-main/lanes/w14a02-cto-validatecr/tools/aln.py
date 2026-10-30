#!/usr/bin/env python3
"""aln.py <m.o> lo hi [local]: orig insns in [lo,hi) with their rm-aligned candidate offset (global or local-window alignment)."""
import sys,os,difflib,re
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from abs import n2
o=orig_dis(); c=cand_dis(sys.argv[1]); lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
if len(sys.argv)>4:
    o=[x for x in o if x[0]<0x1a88]
    k=next(i for i,(a,t) in enumerate(c) if re.match(r'j(eq|ne) r\d, 0x2, ',t))-1; c=c[:k]
sm=difflib.SequenceMatcher(None,[n2(t) for _,t in o],[n2(t) for _,t in c],autojunk=False)
m={}
for a,b,n in sm.get_matching_blocks():
    for k in range(n): m[a+k]=b+k
for i,(a,t) in enumerate(o):
    if lo<=a<hi: print('%5x %-40s %s'%(a,t,('%5x %s'%(c[m[i]][0],c[m[i]][1])) if i in m else '   --'))
