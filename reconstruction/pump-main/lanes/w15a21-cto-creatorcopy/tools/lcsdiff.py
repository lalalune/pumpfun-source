#!/usr/bin/env python3
"""lcsdiff.py <ref> <cand> [--mask rfj] : orig offsets matched (true LCS) by cand but not ref (+) and vice versa (-)"""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
exec(open(T+'/lcschunk.py').read().split('a=sys.argv')[0].split('from fact import mk')[1])
a=sys.argv[1:]; m='rfj'
if '--mask' in a: i=a.index('--mask'); m=a[i+1]; del a[i:i+2]
f=mk(m[0]=='r',m[1]=='f',m[2]=='j'); O=oracle.orig_window(); ot,oo=xled.toks(O); A=f(ot)
def h(p):
    C=xled.load(f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,_=xled.toks(C); return matched(A,f(ct))
r=h(a[0]); c=h(a[1])
print('+',' '.join(f'{o:x}' for x,y,o in zip(r,c,oo) if y and not x))
print('-',' '.join(f'{o:x}' for x,y,o in zip(r,c,oo) if x and not y))
