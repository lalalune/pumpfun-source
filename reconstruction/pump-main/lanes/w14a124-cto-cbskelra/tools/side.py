#!/usr/bin/env python3
"""side.py <cand> <orig_lo> <orig_hi>: skeleton-aligned side-by-side disassembly of an orig range vs cand.
Marks: ' ' M-equal, 'r' equal after reg mask, 's' skeleton-equal only, '-' orig-only, '+' cand-only."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
import dis as D
p=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
O=oracle.orig_window(); C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
ot,oo=xled.toks(O); ct,co=xled.toks(C); od=dict(D.d(O)); cd=dict(D.d(C))
rm=lambda t:[bytes([x[0],0])+x[2:] for x in t]
a=xled.fmask(ot); b=xled.fmask(ct)
for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
    anc=oo[i1] if i1<len(oo) else 1<<30
    if tag!='equal' and not (lo<=anc<hi or (i2>i1 and lo<=oo[i2-1]<hi)): continue
    if tag=='equal':
        for k in range(i2-i1):
            i=i1+k; j=j1+k
            if not(lo<=oo[i]<hi): continue
            m=' ' if ot[i]==ct[j] else ('r' if rm([ot[i]])==rm([ct[j]]) else 's')
            print(f'{m} {oo[i]:05x} {od.get(oo[i],"?"):42s} | {co[j]:05x} {cd.get(co[j],"?")}')
    else:
        n=max(i2-i1,j2-j1)
        for k in range(n):
            l=f'{oo[i1+k]:05x} {od.get(oo[i1+k],"?"):42s}' if i1+k<i2 else ' '*48
            r=f'{co[j1+k]:05x} {cd.get(co[j1+k],"?")}' if j1+k<j2 else ''
            print(f'{"-" if i1+k<i2 and j1+k>=j2 else ("+" if i1+k>=i2 else "x")} {l} | {r}')
