#!/usr/bin/env python3
"""ufclass.py <ra.log> <vreg>: pre-coalescing vregs that the RegisterCoalescer merged into vreg's final class (experiment only)."""
import sys,re
log=open(sys.argv[1]).read(); s=log.index('REGISTER COALESCER'); e=log.index('GREEDY REGISTER ALLOCATION')
par={}
def f(x):
    while par.get(x,x)!=x: x=par[x]
    return x
for a,b in re.findall(r'Success: (%\d+) -> (%\d+)',log[s:e]):
    par[f(a)]=f(b)
t=f(sys.argv[2]); print(' '.join(sorted({k for k in list(par)+list(par.values()) if f(k)==t},key=lambda x:int(x[1:]))))
