#!/usr/bin/env python3
"""tp2.py <fn.bin|main>...: w16 skeleton transplant2 (per-region perfect / skeleton-only transplant deltas) on any fn.bin."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled
exec(open(os.path.join(T,'regions2.py')).read())
O=oracle.orig_window(); ot,oo=xled.toks(O); a=xled.fmask(ot)
def ratio(o,c): return difflib.SequenceMatcher(None,o,c,autojunk=False).ratio()
for p in sys.argv[1:]:
    C=xled.load(p if p=='main' or p.endswith('.bin') else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,co=xled.toks(C); b=xled.fmask(ct)
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False); amap={}
    for bl in sm.get_matching_blocks():
        for k in range(bl.size): amap[bl.a+k]=bl.b+k
    base=ratio(ot,ct); out=[]
    for lo,hi,n in R:
        ii=[i for i,o in enumerate(oo) if lo<=o<hi]; i0=ii[0]; i1=ii[-1]
        prev=max([amap[i] for i in range(0,i0) if i in amap],default=-1); nxt=min([amap[i] for i in range(i1+1,len(ot)) if i in amap],default=len(ct))
        j0,j1=prev+1,nxt
        r=ratio(ot,ct[:j0]+ot[i0:i1+1]+ct[j1:])
        out.append('%s:%+.4f'%(hex(lo),r-base))
    print(os.path.basename(os.path.dirname(p)) if '/' in p else p,'%.5f'%base,len(C),' '.join(out),flush=True)
