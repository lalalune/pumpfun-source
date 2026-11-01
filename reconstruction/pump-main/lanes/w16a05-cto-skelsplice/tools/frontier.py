#!/usr/bin/env python3
"""frontier.py <idx.npz> <orig_hex_boundary> [--top N]: for one orig boundary, every build's front gain (orig tokens
[0,k) matched minus main's) and back gain ([k,N)); prints the Pareto frontier (max back for each front gain)."""
import sys,os
import numpy as np
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled
from env import main_partners
LANES=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes')
O=oracle.orig_window(); OT,OO=xled.toks(O); OO=np.array(OO)
a=sys.argv[1:]; top=30
if '--top' in a: i=a.index('--top'); top=int(a[i+1]); del a[i:i+2]
Z=np.load(a[0]); names=[os.path.relpath(str(x),LANES).replace('/rx/','/').replace('/fn.bin','') for x in Z['names']]; nb=Z['nbytes']
hit=Z['MP']>=0; mm=main_partners()>=0
k=int(np.searchsorted(OO,int(a[1],16)))
fg=hit[:,:k].sum(1)-mm[:k].sum(); bg=hit[:,k:].sum(1)-mm[k:].sum()
print(f'boundary orig {OO[k]:#x} (tok {k}); main front {mm[:k].sum()} back {mm[k:].sum()}')
o=np.lexsort((-bg,-fg)); best=-10**9; n=0
print(' front  back  total  bytes  build')
for j in o:
    if bg[j]>best:
        best=bg[j]; print(f'{fg[j]:+6d} {bg[j]:+5d} {fg[j]+bg[j]:+6d} {nb[j]:6d}  {names[j]}'); n+=1
    if n>=top: break
