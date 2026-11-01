#!/usr/bin/env python3
"""chunkmask.py <fn.bin>...: true-LCS totals under masks ---, -f-, r--, rf-, rfj and per-0x800 orig chunk deltas vs the first file."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled
from fact import mk
from lcs import lcs
from lcschunk_m import matched_ops
ot,oo=xled.toks(oracle.orig_window())
def st(p):
    ct,_=xled.toks(open(p,'rb').read()); r={}
    for m in ('---','-f-','r--','rf-','rfj'):
        f=mk(m[0]=='r',m[1]=='f',m[2]=='j'); r[m]=lcs(f(ot),f(ct))
    return r
base=None
for p in sys.argv[1:]:
    s=st(p)
    if base is None: base=s; print(p,' '.join(f'{k}:{v}' for k,v in s.items()))
    else: print(p,' '.join(f'{k}:{v}({v-base[k]:+d})' for k,v in s.items()))
