#!/usr/bin/env python3
"""side.py <cand.bin> <orig_lo> <orig_hi> <cand_lo> <cand_hi> [--mode N]: local side-by-side alignment of an original range
against a candidate range (difflib on skel tokens of the given mode; '=' exact m0 equality). Experiment only."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import d as D, skel, oracle
a=sys.argv[1:]; mode=3
if '--mode' in a: k=a.index('--mode'); mode=int(a[k+1]); del a[k:k+2]
cb=D.load(a[0]); olo,ohi,clo,chi=[int(x,16) for x in a[1:5]]
O=oracle.orig_window(); od=D.dis(O); cd=D.dis(cb)
to=skel.toks(O,mode); tc=skel.toks(cb,mode); e0=skel.toks(O,0); c0=skel.toks(cb,0)
oi=[i for i,(o,_) in enumerate(od) if olo<=o<ohi]; ci=[i for i,(o,_) in enumerate(cd) if clo<=o<chi]
sm=difflib.SequenceMatcher(None,[to[i] for i in oi],[tc[i] for i in ci],autojunk=False)
ne=0
for op,i1,i2,j1,j2 in sm.get_opcodes():
    n=max(i2-i1,j2-j1)
    for k in range(n):
        x=oi[i1+k] if i1+k<i2 else None; y=ci[j1+k] if j1+k<j2 else None
        L=f'{od[x][0]:#06x} {od[x][1]}' if x is not None else ''
        R=f'{cd[y][0]:#06x} {cd[y][1]}' if y is not None else ''
        mk='=' if (x is not None and y is not None and e0[x]==c0[y]) else ('~' if op=='equal' else ' ')
        ne+=mk=='='
        print(f'{L:<40} {mk} {R}')
print('exact',ne,'orig',len(oi),'cand',len(ci))
