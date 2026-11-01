#!/usr/bin/env python3
"""mask.py <name>...: exact M and register/frame/jump-masked M vs the original (structure proxy)"""
import sys,os,difflib,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
OUT=os.path.dirname(T)
def toks(raw,mode):
    out=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; b=bytearray(raw[i:i+n]); op=b[0]; cls=op&7
        if op==0x85: b[1]&=0x0f; b[4:8]=b'\0'*4
        if op==0x18: b[4:8]=b'\0'*4; b[12:16]=b'\0'*4
        if mode>=1:
            src=b[1]>>4; dst=b[1]&15
            fr = (cls==1 and src==10) or (cls in (2,3) and dst==10)
            if fr: b[2:4]=b'\0\0'
            if cls==5 and op not in (0x85,0x95): b[2:4]=b'\0\0'
        if mode>=2:
            b[1]=0 if op!=0x85 else b[1]&0x0f
        out.append(bytes(b)); i+=n
    return out
ow=oracle.orig_window()
for n in sys.argv[1:]:
    p=n if os.path.exists(n) else f'{OUT}/fx/{n}/fn.bin'
    raw=open(p,'rb').read(); r=[]
    for mode in (0,1,2):
        a=toks(ow,mode); c=toks(raw,mode)
        sm=difflib.SequenceMatcher(None,a,c,autojunk=False); r.append(sum(x.size for x in sm.get_matching_blocks()))
    print(f'{n:10s} bytes {len(raw)} exact {r[0]} frame+jump-masked {r[1]} +reg-masked {r[2]}')
