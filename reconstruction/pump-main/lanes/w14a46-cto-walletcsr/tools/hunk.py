#!/usr/bin/env python3
"""hunk.py <a.dis> <b.dis> [max]: difflib hunks between two disassemblies under wf2 normalisation (frame/jump masked)."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__))
g={'__file__':T+'/wf2.py'}; exec(open(T+'/wf2.py').read().split("O=rd(")[0],g)
A=g['rd'](open(sys.argv[1])); B=g['rd'](open(sys.argv[2])); mx=int(sys.argv[3]) if len(sys.argv)>3 else 40
sm=difflib.SequenceMatcher(None,[x[1] for x in A],[x[1] for x in B],autojunk=False); k=0
for op,a1,a2,b1,b2 in sm.get_opcodes():
    if op=='equal': continue
    k+=1
    if k>mx: continue
    print('%s a[%04x..%04x) %d  b[%04x..%04x) %d'%(op,A[a1][0] if a1<len(A) else 0,A[a2-1][0] if a2>a1 else 0,a2-a1,B[b1][0] if b1<len(B) else 0,B[b2-1][0] if b2>b1 else 0,b2-b1))
    for i in range(a1,min(a2,a1+6)): print('   - %04x %s'%A[i])
    for i in range(b1,min(b2,b1+6)): print('   + %04x %s'%B[i])
print('hunks',k)
