#!/usr/bin/env python3
"""offmap.py <candA> <candB> [lo hi]: align each (frame-masked) to orig; for orig r10 accesses in [lo,hi) print orig off, A off, B off; histogram of (A->B) off changes."""
import sys,os,difflib,struct,collections
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
def fm(t):
    out=[]
    for x in t:
        x=bytearray(x); op=x[0]; cl=op&7
        if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): x[2:4]=b'\0\0'
        if op==0x07: x[4:8]=b'\0'*4
        out.append(bytes(x))
    return out
O=oracle.orig_window(); ot=oracle.mask(O)
def ld(p): return oracle.mask(xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'))
def off(x):
    op=x[0]; cl=op&7
    if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): return struct.unpack_from('<h',x,2)[0]
    return None
def amap(c):
    sm=difflib.SequenceMatcher(None,fm(ot),fm(c),autojunk=False); m={}
    for a,b,n in sm.get_matching_blocks():
        for k in range(n): m[a+k]=b+k
    return m
A=ld(sys.argv[1]); B=ld(sys.argv[2]); lo=int(sys.argv[3],16)//8 if len(sys.argv)>3 else 0; hi=min(len(ot),int(sys.argv[4],16)//8) if len(sys.argv)>4 else len(ot)
ma=amap(A); mb=amap(B); h=collections.Counter(); hb=collections.Counter()
for i in range(lo,hi):
    o=off(ot[i])
    if o is None or i not in ma or i not in mb: continue
    a=off(A[ma[i]]); b=off(B[mb[i]])
    h[(o==a,o==b)]+=1
    if o!=b: hb[(b,o)]+=1
print('(A ok, B ok) counts',dict(h))
print('B off -> orig off (top):',[(hex(-x&0xffff),hex(-y&0xffff),n) for (x,y),n in hb.most_common(25)])
