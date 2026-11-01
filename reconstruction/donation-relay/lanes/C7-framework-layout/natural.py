#!/usr/bin/env python3
"""natural.py <unstripped.so>: target function table in address order, with candidate address, symbol and hash, marking order breaks."""
import sys,os
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/relay/tools'))
import relay
from relaylib import *
cand=sys.argv[1]
t,c,sy,tf,tn,cn,pair,idx=relay.compare(cand)
names=relay.delta_names()
prev=None
for a,s in tf:
    b=pair.get(a)
    nm=demangle(sy[b][1]) if b is not None else '-- '+(names.get(a,{}).get('name') or '?')
    h=sy[b][1][-20:-1] if b is not None else ''
    print(f"{a:#8x} {s:6d} {('%#8x'%b) if b is not None else '       -'} {'' if (b is None or prev is None or b>prev) else 'BACK'} {nm[:150]} {h}")
    if b is not None: prev=b
