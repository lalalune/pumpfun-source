#!/usr/bin/env python3
"""vdiff.py <m.o> [lo hi]: rm-normalized (n2) alignment of orig vs cand, print non-equal hunks touching orig [lo,hi)."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from abs import n1,n2
o=orig_dis(); c=cand_dis(sys.argv[1]); lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 0x1800
sm=difflib.SequenceMatcher(None,[n2(t) for _,t in o],[n2(t) for _,t in c],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    if i1<len(o) and not (lo<=o[min(i1,len(o)-1)][0]<hi): continue
    print('== %s orig %x-%x (%d)  cand %x-%x (%d)'%(tag,o[i1][0] if i1<len(o) else 0,o[i2-1][0] if i2>i1 else 0,i2-i1,c[j1][0] if j1<len(c) else 0,c[j2-1][0] if j2>j1 else 0,j2-j1))
    for k in range(max(i2-i1,j2-j1)):
        a='%5x %-36s'%(o[i1+k][0],o[i1+k][1][:36]) if i1+k<i2 else ' '*42
        b='%5x %s'%(c[j1+k][0],c[j1+k][1][:40]) if j1+k<j2 else ''
        print('  ',a,'|',b)
