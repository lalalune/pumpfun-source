#!/usr/bin/env python3
"""hitdiff.py <A> <B> [lo hi]: original tokens matched (M, scorer mask) by A but not B and vice versa, with orig disassembly."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import regprof,oracle,numpy as np
import sdis as D
a,b=sys.argv[1],sys.argv[2]; lo=int(sys.argv[3],16) if len(sys.argv)>3 else 0; hi=int(sys.argv[4],16) if len(sys.argv)>4 else 1<<30
ha,_=regprof.hits(a); hb,_=regprof.hits(b); OO=np.array(regprof.OO); od=dict(D.d(oracle.orig_window()))
for i in range(len(OO)):
    if not(lo<=OO[i]<hi): continue
    if ha[i]!=hb[i]: print(f"{'A' if ha[i] else 'B'} {OO[i]:05x} {od.get(int(OO[i]),'?')}")
