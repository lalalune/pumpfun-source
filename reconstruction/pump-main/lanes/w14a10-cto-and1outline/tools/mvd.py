#!/usr/bin/env python3
"""mvd.py a b [lo]: align two candidates (regs/imms masked) and print where the offset delta changes (size moves), from cand-a offset lo."""
import sys,os,re,difflib
sys.path.insert(0,os.path.dirname(__file__))
from slots import cand_dis
from pbk import norm
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def rn(t): return re.sub(r'r\d+','R',re.sub(r'0x[0-9a-f]+','X',norm(t)))
A=cand_dis(O+'/rx/%s/m.o'%sys.argv[1]); B=cand_dis(O+'/rx/%s/m.o'%sys.argv[2]); lo=int(sys.argv[3],16) if len(sys.argv)>3 else 0
sm=difflib.SequenceMatcher(None,[rn(t) for _,t in A],[rn(t) for _,t in B],autojunk=False)
prev=None
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    if A[min(i1,len(A)-1)][0]<lo: continue
    print('%-7s a %5x+%d  b %5x+%d'%(tag,A[min(i1,len(A)-1)][0],(i2-i1)*8,B[min(j1,len(B)-1)][0],(j2-j1)*8))
    for k in range(i1,min(i2,i1+4)): print('      a: ',A[k][1])
    for k in range(j1,min(j2,j1+4)): print('      b: ',B[k][1])
