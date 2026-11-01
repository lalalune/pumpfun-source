#!/usr/bin/env python3
"""mm.py <fn.bin>...: exact M and masked M (regs, r10 offsets, jump offsets masked) vs original."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,fx
def maskx(raw):
    m=bytearray(raw); i=0; toks=[]
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8
        t=bytearray(raw[i:i+n])
        if op==0x85: t[1]&=0x0f; t[4:8]=b'\0'*4
        if op==0x18: t[4:8]=b'\0'*4; t[12:16]=b'\0'*4
        cls=op&7
        t[1]=0  # regs
        if cls in (1,2,3): t[2:4]=b'\0\0'  # mem offsets
        if cls==5: t[2:4]=b'\0\0'          # jump offsets
        toks.append(bytes(t)); i+=n
    return toks
O=None
def Mx(b):
    global O
    if O is None: O=maskx(oracle.orig_window())
    c=maskx(b); sm=difflib.SequenceMatcher(None,O,c,autojunk=False); return sum(x.size for x in sm.get_matching_blocks())
for p in sys.argv[1:]:
    b=open(p,'rb').read(); print(p.split('/')[-2], 'M',fx.Mof(b)[0],'Mmask',Mx(b),'bytes',len(b))
