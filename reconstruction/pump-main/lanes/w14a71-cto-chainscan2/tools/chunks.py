#!/usr/bin/env python3
"""chunks.py a.bin b.bin [chunk_insns]: per original chunk, number of original tokens matched (difflib) by a and b."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
O=G['mask'](G['orig_window']()); n=int(sys.argv[3]) if len(sys.argv)>3 else 256
def per(f):
    c=G['mask'](open(f,'rb').read()); m=[0]*(len(O)//n+1)
    for a,b,s in difflib.SequenceMatcher(None,O,c,autojunk=False).get_matching_blocks():
        for k in range(a,a+s): m[k//n]+=1
    return m
A=per(sys.argv[1]); B=per(sys.argv[2])
for i,(x,y) in enumerate(zip(A,B)):
    if x!=y: print('chunk %3d (orig tok %5d..) a %4d b %4d  %+d'%(i,i*n,x,y,y-x))
print('total',sum(A),sum(B))
