#!/usr/bin/env python3
"""mj.py <name>...: M with (a) scorer mask, (b) + jump offsets masked, (c) + regs masked, (d) + frame offsets masked."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
OUT=os.path.dirname(T)
def toks(raw,j=False,r=False,f=False):
    out=[]
    for t in oracle.mask(raw):
        b=bytearray(t); op=b[0]
        if j and (op&7)==5 and op not in (0x85,0x95): b[2:4]=b'\0\0'
        if r and op!=0x85: b[1]=0
        if f and (op&7) in (1,2,3): b[2:4]=b'\0\0'
        out.append(bytes(b))
    return out
ow=oracle.orig_window()
def M(raw,**k):
    a=toks(ow,**k); c=toks(raw,**k)
    return sum(x.size for x in difflib.SequenceMatcher(None,a,c,autojunk=False).get_matching_blocks())
for n in sys.argv[1:]:
    p=n if os.path.exists(n) else f'{OUT}/fx/{n}/fn.bin'; raw=open(p,'rb').read()
    print(n,len(raw),'M',M(raw),'Mj',M(raw,j=True),'Mjr',M(raw,j=True,r=True),'Mjrf',M(raw,j=True,r=True,f=True))
