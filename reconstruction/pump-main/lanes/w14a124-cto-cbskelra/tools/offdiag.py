#!/usr/bin/env python3
"""offdiag.py <cand> [mask]: per anchored segment, scorer-M matches under the GLOBAL difflib alignment (counted on orig
tokens of the segment) vs the anchored segment-pair M. Large anchored>global = global alignment off-diagonal there."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from segcmp import load,fm,rm
import segall
p=sys.argv[1]; R=segall.prof(p)
O=load('orig'); C=load(p); om=oracle.mask(O); cm=oracle.mask(C)
h=[0]*len(om); pair=[-1]*len(om)
for bl in difflib.SequenceMatcher(None,om,cm,autojunk=False).get_matching_blocks():
    for k in range(bl.size): h[bl.a+k]=1; pair[bl.a+k]=bl.b+k
pos=0; tg=ta=0; out=[]
for r in R:
    g=sum(h[pos:pos+r['no']]); out.append((r['v'][0]-g,r,g)); pos+=r['no']; tg+=g; ta+=r['v'][0]
print('global M',tg,'anchored M',ta)
for d,r,g in sorted(out,key=lambda x:-x[0])[:15]: print(f"  seg {r['k']:3d} o {r['o']:05x} c {r['c']:05x} n {r['no']}/{r['nc']} anchoredM {r['v'][0]} globalM {g} d {d:+d}")
for d,r,g in sorted(out,key=lambda x:x[0])[:8]: print(f"  (global>anch) seg {r['k']:3d} o {r['o']:05x} n {r['no']}/{r['nc']} anchoredM {r['v'][0]} globalM {g} d {d:+d}")
