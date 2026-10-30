#!/usr/bin/env python3
"""cdiff.py a.o b.o: opcode-level diff summary of two candidates (regs/frame masked), listing changed hunks with offsets."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__))
from slots import cand_dis
from abs import n2
a=cand_dis(sys.argv[1]); b=cand_dis(sys.argv[2])
sm=difflib.SequenceMatcher(None,[n2(t) for _,t in a],[n2(t) for _,t in b],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag!='equal':
        print(tag,'a[%x:%x] %d'%(a[i1][0] if i1<len(a) else -1, a[i2-1][0] if i2>i1 else -1,i2-i1),'b[%x:%x] %d'%(b[j1][0] if j1<len(b) else -1,b[j2-1][0] if j2>j1 else -1,j2-j1))
