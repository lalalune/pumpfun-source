#!/usr/bin/env python3
"""skops.py <cand> [lo hi]: skeleton (fmask) difflib opcodes orig vs cand, restricted to orig range."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
p=sys.argv[1]; lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 1<<30
O=oracle.orig_window(); C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
ot,oo=xled.toks(O); ct,co=xled.toks(C)
a=xled.fmask(ot); b=xled.fmask(ct)
for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
    oa=oo[i1] if i1<len(oo) else len(O); ca=co[j1] if j1<len(co) else len(C)
    if not (lo<=oa<hi): continue
    print(f'{tag:7s} o {oa:05x} n{i2-i1:4d}  c {ca:05x} n{j2-j1:4d}  delta {ca-oa:+x}')
