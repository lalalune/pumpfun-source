#!/usr/bin/env python3
"""spans.py A.o B.o [mask]: orig spans (>=4 instrs) rm-matched in B but not in A, and vice versa, with cand addrs."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from abs import n1,n2
o=orig_dis(); f=n2
def mp(p):
    c=cand_dis(p); sm=difflib.SequenceMatcher(None,[f(t) for _,t in o],[f(t) for _,t in c],autojunk=False)
    m={}
    for a,b,n in sm.get_matching_blocks():
        for k in range(n): m[a+k]=c[b+k][0]
    return m
A,B=mp(sys.argv[1]),mp(sys.argv[2])
def runs(pred):
    r=[];s=None
    for i in range(len(o)):
        if pred(i):
            if s is None: s=i
        else:
            if s is not None and i-s>=4: r.append((s,i))
            s=None
    return r
for nm,pred,M in (('gained',lambda i:i in B and i not in A,B),('lost',lambda i:i in A and i not in B,A)):
    rr=runs(pred); print(nm,sum(e-s for s,e in rr))
    for s,e in rr: print('   orig %5x-%5x n=%3d  cand %5x  first: %s'%(o[s][0],o[e-1][0],e-s,M[s],o[s][1]))
