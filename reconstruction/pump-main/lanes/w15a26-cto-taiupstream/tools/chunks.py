#!/usr/bin/env python3
"""chunks.py a.bin b.bin [step]: per-orig-chunk matched-token counts (scorer mask) for two candidates, and the delta."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); g={'__name__':'x'}; exec(src.split("OUT=os.environ")[0],g)
Ob=open(T+'/orig.bin','rb').read(); ot=g['mask'](Ob)
off=[];i=0
for x in ot: off.append(i); i+=len(x)
step=int(sys.argv[3],0) if len(sys.argv)>3 else 0x400
FM=os.environ.get('FM')
def fm(t):
    out=[]
    for x in t:
        x=bytearray(x); op=x[0]; cl=op&7
        if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): x[2:4]=b'\0\0'
        if op==0x07: x[4:8]=b'\0'*4
        out.append(bytes(x))
    return out
if FM: ot=fm(ot)
def hits(f):
    ct=g['mask'](open(f,'rb').read()); ct=fm(ct) if FM else ct; h=[0]*len(ot)
    for bl in difflib.SequenceMatcher(None,ot,ct,autojunk=False).get_matching_blocks():
        for k in range(bl.size): h[bl.a+k]=1
    return h
A=hits(sys.argv[1]); B=hits(sys.argv[2])
for c in range(0,len(Ob),step):
    idx=[i for i in range(len(ot)) if c<=off[i]<c+step]
    a=sum(A[i] for i in idx); b=sum(B[i] for i in idx)
    if a!=b: print(f'{c:#06x} n={len(idx):4d} a={a:4d} b={b:4d} d={b-a:+d}')
print('total',sum(A),sum(B))
