#!/usr/bin/env python3
"""amap.py <obj|.bin> lo hi: for orig [lo,hi), print each orig run of tokens and what our pc range it aligns to (global SequenceMatcher), plus unmatched gaps."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
O=G['orig_window'](); p=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
c=open(p,'rb').read() if p.endswith('.bin') else G['elf_fn'](p,G['KEEP'])
def pcs(raw):
    r=[];pc=0
    for t in G['mask'](raw): r.append(pc); pc+=len(t)
    return r
ot=G['mask'](O); ct=G['mask'](c); op=pcs(O); cp=pcs(c)
sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
for b in sm.get_matching_blocks():
    if b.size==0: continue
    a0=op[b.a]; a1=op[b.a+b.size-1]
    if a1<lo or a0>=hi: continue
    print('orig %#06x-%#06x (%3d) <- ours %#06x-%#06x'%(a0,a1,b.size,cp[b.b],cp[b.b+b.size-1]))
