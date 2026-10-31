#!/usr/bin/env python3
"""xtab.py <cand> : one line per ours-only / orig-only run (n>=2) with landmarks: nearest error line imm before/after, calls inside, ops summary"""
import sys,os,re,io,contextlib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import xled,oracle
import dis as D
p=sys.argv[1]; p=p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'
buf=io.StringIO()
with contextlib.redirect_stdout(buf): xled.run(p,2,True)
txt=buf.getvalue().split('\n')
def lm(raw):
    L=D.d(raw); lines=[]
    for o,s in L:
        m=re.match(r'stw \[r10-0x2b8\], (\d+)',s)
        if m: lines.append((o,int(m.group(1))))
    return L,lines
C=xled.load(p); O=oracle.orig_window()
for side,raw,hdr in (('ours',C,'cand '),('orig',O,'orig ')):
    L,lines=lm(raw); dd=dict(L)
    print(f'## {side}-only runs')
    tot=0
    for l in txt:
        if not l.startswith(hdr): continue
        a,b=[int(x,16) for x in l.split()[1].split('-')]; n=int(re.search(r'n=\s*(\d+)',l).group(1)); tot+=n
        prev=[ln for o,ln in lines if o<a][-1:] ; nxt=[ln for o,ln in lines if o>=a][:1]
        ops=[dd[o].split()[0] for o in sorted(dd) if a<=o<b]
        calls=[dd[o] for o in sorted(dd) if a<=o<b and dd[o].startswith('call')]
        from collections import Counter
        cs=' '.join(f'{k}x{v}' for k,v in Counter(ops).most_common(5))
        print(f'{a:05x}-{b:05x} n={n:3d} B={8*n:4d} err-before {prev} err-after {nxt} calls {len(calls)} | {cs}')
    print('total tok',tot)
