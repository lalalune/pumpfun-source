#!/usr/bin/env python3
"""skel.py <fn.bin|orig>...: scorer-style M vs the original at mask levels:
 m0 = scorer (call imm + lddw imm masked); m1 = + r10 frame offsets / r10 add imms masked; m2 = + jump offsets masked; m3 = + registers masked."""
import sys,difflib,os,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import d as D, oracle
def toks(raw,mode):
    out=[]; i=0
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8
        t=bytearray(raw[i:i+n]); cls=op&7; dst=t[1]&0xf; src=t[1]>>4
        if op==0x85: t[1]&=0x0f; t[4:8]=b'\0'*4
        if op==0x18: t[4:8]=b'\0'*4; t[12:16]=b'\0'*4
        if mode>=1:
            if cls in (1,) and src==10: t[2:4]=b'\0\0'
            if cls in (2,3) and dst==10: t[2:4]=b'\0\0'
            if op==0x07 and dst==10: pass
            if op==0x07: t[4:8]=b'\0'*4 if struct.unpack_from('<i',raw,i+4)[0]<0 else t[4:8]
        if mode>=2 and cls in (5,6) and op not in (0x85,0x95,0x8d): t[2:4]=b'\0\0'
        if mode>=3: t[1]=0
        out.append(bytes(t)); i+=n
    return out
O=oracle.orig_window()
def M(b,mode):
    sm=difflib.SequenceMatcher(None,toks(O,mode),toks(b,mode),autojunk=False)
    return sum(x.size for x in sm.get_matching_blocks())
if __name__=='__main__':
    for p in sys.argv[1:]:
        b=D.load(p)
        print('%-14s'%(os.path.basename(os.path.dirname(p)) or p), len(b), ' '.join('m%d=%d'%(k,M(b,k)) for k in (0,1,2,3)),flush=True)
