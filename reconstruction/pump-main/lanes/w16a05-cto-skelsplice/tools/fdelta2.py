#!/usr/bin/env python3
"""fdelta2.py <build>...: per region, frame-offset deltas (orig - cand) of skeleton-matched frame accesses, plus how many
cand frame offsets differ from main's for the SAME orig access (frame naming moved vs main)."""
import sys,os,difflib,struct
from collections import Counter,defaultdict
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled
from regs import R,reg
from regprof import path
O=oracle.orig_window(); ot,oo=xled.toks(O); OF=xled.fmask(ot)
def foff(x):
    op=x[0]; cl=op&7
    if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): return struct.unpack('<h',x[2:4])[0]
    return None
def fmap(p):
    C=xled.load(path(p)); ct,_=xled.toks(C); m={}
    for bl in difflib.SequenceMatcher(None,OF,xled.fmask(ct),autojunk=False).get_matching_blocks():
        for k in range(bl.size):
            i=bl.a+k; fx=foff(ot[i]); fy=foff(ct[bl.b+k])
            if fx is not None and fy is not None: m[i]=fy
    return m
mm=fmap('main')
for p in sys.argv[1:]:
    m=fmap(p); print('==',p)
    h=defaultdict(Counter); vs=defaultdict(Counter)
    for i,fy in m.items():
        n=reg(oo[i]); h[n][foff(ot[i])-fy]+=1
        if i in mm: vs[n]['same' if mm[i]==fy else 'moved']+=1
    for lo,hi,n in R:
        c=h[n]; t=sum(c.values())
        if not t: continue
        top=', '.join(f'{d:+d}:{v}' for d,v in c.most_common(5))
        print(f'  {n:13s} acc {t:4d} orig-eq {c[0]:4d}  vs-main same {vs[n]["same"]:4d} moved {vs[n]["moved"]:4d}   deltas {top}')
