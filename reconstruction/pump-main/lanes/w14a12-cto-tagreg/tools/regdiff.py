#!/usr/bin/env python3
"""regdiff.py <a.fn.bin|so> <b.fn.bin|so> [seg]: per-orig-region plain / frame-masked matched-token counts, a vs b."""
import sys,os,difflib,collections
T=os.path.dirname(os.path.abspath(__file__)); src=open(T+'/rx.py').read(); g={}; exec(src.split("OUT=os.environ")[0],g)
def ld(p): return g['elf_fn'](p,g['KEEP']) if p.endswith('.so') else open(p,'rb').read()
def split(r):
    out=[];i=0
    while i<len(r):
        n=16 if r[i]==0x18 else 8; b=bytearray(r[i:i+n])
        if b[0]==0x85: b[1]&=0x0f; b[4:8]=b'\0'*4
        if b[0]==0x18: b[4:8]=b'\0'*4; b[12:16]=b'\0'*4
        out.append(bytes(b)); i+=n
    return out
def fm(t):
    b=bytearray(t)
    if (b[1]&0xf)==10 or (b[1]>>4)==10: b[2:4]=b'\0\0'
    return bytes(b)
O=split(g['orig_window']()); OFF=[];o=0
for t in O: OFF.append(o); o+=len(t)
seg=int(sys.argv[3],16) if len(sys.argv)>3 else 0x400
def reg(c,f):
    R=collections.Counter(); sm=difflib.SequenceMatcher(None,[f(t) for t in O],[f(t) for t in c],autojunk=False)
    for a,b,s in sm.get_matching_blocks():
        for k in range(s): R[OFF[a+k]//seg]+=1
    return R
A=split(ld(sys.argv[1])); B=split(ld(sys.argv[2]))
pa,pb,fa,fb=reg(A,lambda t:t),reg(B,lambda t:t),reg(A,fm),reg(B,fm)
for k in sorted(set(pa)|set(pb)|set(fa)|set(fb)):
    d1=pb[k]-pa[k]; d2=fb[k]-fa[k]
    if d1 or d2: print(hex(k*seg), 'plain %+d'%d1, 'fm %+d'%d2)
print('total plain %+d fm %+d'%(sum(pb.values())-sum(pa.values()), sum(fb.values())-sum(fa.values())))
