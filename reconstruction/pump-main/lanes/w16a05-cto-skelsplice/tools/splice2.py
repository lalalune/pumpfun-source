#!/usr/bin/env python3
"""splice2.py <front> <back> <orig_hex>... : exact M of front-of-A + back-of-B cut at the first orig token >= addr aligned
in both (w14a09 splice.py generalised to any fn.bin/.so/lane-name), with bytes, calls and error-line multiset check.
splice2.py --three <A> <B> <lo_hex> <hi_hex>: A[0:lo] + B[lo:hi] + A[hi:] (an insert of B's middle into A)."""
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
def M(c): return sum(b.size for b in difflib.SequenceMatcher(None,OT,[oracle.mask(t)[0] for t in c],autojunk=False).get_matching_blocks())
def report(tag,c):
    calls,lines=sig(c); ld=sum(((lines-OL)+(OL-lines)).values())
    print(f'{tag}: M {M(c)} bytes {sum(len(t) for t in c)} calls {calls} line_diff {ld}')
if __name__=='__main__':
    a=sys.argv[1:]; three='--three' in a; a=[x for x in a if x!='--three']
    F=raw(a[0]); B=raw(a[1]); mf=amap([oracle.mask(t)[0] for t in F]); mb=amap([oracle.mask(t)[0] for t in B])
    cut=lambda A: next(i for i in range(len(OT)) if OO[i]>=A and i in mf and i in mb)
    print('A M',len(mf),'B M',len(mb))
    if three:
        k1=cut(int(a[2],16)); k2=cut(int(a[3],16))
        report(f'A[0:{OO[k1]:#x}] + B[{OO[k1]:#x}:{OO[k2]:#x}] + A[{OO[k2]:#x}:]',F[:mf[k1]]+B[mb[k1]:mb[k2]]+F[mf[k2]:])
    else:
        for s in a[2:]:
            k=cut(int(s,16)); report(f'cut orig {OO[k]:#x}',F[:mf[k]]+B[mb[k]:])
