#!/usr/bin/env python3
"""regM.py lo hi <cand>...: matched orig tokens inside orig [lo,hi) under the global difflib alignment, per mask level."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from segcmp import fm,rm,jm
lo=int(sys.argv[1],16); hi=int(sys.argv[2],16)
O=oracle.orig_window(); ot,oo=xled.toks(O); om=oracle.mask(O)
for p in sys.argv[3:]:
    C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,co=xled.toks(C); cm=oracle.mask(C)
    out=[]
    for nm,f in (('M',lambda t:t),('rM',rm),('fM',fm),('rfM',lambda t:rm(fm(t))),('rfjM',lambda t:jm(rm(fm(t)))),('skM',xled.fmask)):
        a=f(om if nm!='skM' else ot); b=f(cm if nm!='skM' else ct)
        n=sum(1 for bl in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks() for k in range(bl.size) if lo<=oo[bl.a+k]<hi)
        out.append(f'{nm} {n}')
    print(p,' '.join(out))
