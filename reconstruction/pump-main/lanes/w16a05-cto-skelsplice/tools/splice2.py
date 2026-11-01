#!/usr/bin/env python3
"""splice2.py <front> <back> <orig_hex>...: exact M of front-of-A + back-of-B cut at the first orig token >= addr aligned
in both (w14a09 splice.py generalised to any fn.bin/.so/lane-name), with bytes, calls and error-line multiset check."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled
from regprof import path
from splcheck import sig,OC,OL
O=oracle.orig_window(); OT,OO=xled.toks(O)
def raw(p):
    b=xled.load(path(p)); t=[];i=0
    while i<len(b):
        n=16 if b[i]==0x18 else 8; t.append(b[i:i+n]); i+=n
    return t
def amap(c):
    m={}
    for bl in difflib.SequenceMatcher(None,OT,c,autojunk=False).get_matching_blocks():
        for k in range(bl.size): m[bl.a+k]=bl.b+k
    return m
F=raw(sys.argv[1]); B=raw(sys.argv[2]); fm=[oracle.mask(t)[0] for t in F]; bm=[oracle.mask(t)[0] for t in B]
mf=amap(fm); mb=amap(bm)
M=lambda c: sum(b.size for b in difflib.SequenceMatcher(None,OT,c,autojunk=False).get_matching_blocks())
print('front M',len(mf),'back M',len(mb))
for s in sys.argv[3:]:
    A=int(s,16); k=next(i for i in range(len(OT)) if OO[i]>=A and i in mf and i in mb)
    c=F[:mf[k]]+B[mb[k]:]; cm=[oracle.mask(t)[0] for t in c]; calls,lines=sig(c)
    ld=sum(((lines-OL)+(OL-lines)).values())
    print(f'cut orig {OO[k]:#x}: M {M(cm)} bytes {sum(len(t) for t in c)} calls {calls} line_diff {ld}')
