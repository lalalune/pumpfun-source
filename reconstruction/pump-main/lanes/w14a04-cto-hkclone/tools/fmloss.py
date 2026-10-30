#!/usr/bin/env python3
"""fmloss.py A.o B.o lo hi: orig instrs fm-matched in A but not in B (and vice versa), with B's aligned text."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from abs import n1,n2
o=orig_dis()
def fmset(p):
    c=cand_dis(p)
    sm=difflib.SequenceMatcher(None,[n2(t) for _,t in o],[n2(t) for _,t in c],autojunk=False)
    al={}
    for a,b,n in sm.get_matching_blocks():
        for k in range(n): al[a+k]=c[b+k]
    return {i for i,(ad,t) in enumerate(o) if i in al and n1(al[i][1])==n1(t)}, al
A,aa=fmset(sys.argv[1]); B,ba=fmset(sys.argv[2]); lo=int(sys.argv[3],16); hi=int(sys.argv[4],16)
for i,(ad,t) in enumerate(o):
    if not lo<=ad<hi: continue
    if i in A and i not in B: print('-%5x %-36s | B %s'%(ad,t,ba[i][1] if i in ba else '-'))
    if i in B and i not in A: print('+%5x %-36s | A %s'%(ad,t,aa[i][1] if i in aa else '-'))
