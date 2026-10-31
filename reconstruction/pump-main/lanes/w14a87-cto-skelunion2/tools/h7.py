#!/usr/bin/env python3
"""h7.py in.ll out.ll: (w14a54/w14a66 h7 hoist, generic) every 7-byte memcpy INTO %target.i.sroa.0 writes %target.sroa.0
instead, and the join's memcpy target.sroa.0 <- target.i.sroa.0 is dropped. Post-opt IR oracle only."""
import sys
t=open(sys.argv[1]).read()
J='call void @llvm.memcpy.p0.p0.i64(ptr noundef nonnull align 1 dereferenceable(7) %target.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %target.i.sroa.0, i64 7, i1 false)'
L=t.split('\n'); n=0; m=0; out=[]
for l in L:
    if l.strip()==J: m+=1; continue
    if 'llvm.memcpy' in l and '(ptr noundef nonnull align 1 dereferenceable(7) %target.i.sroa.0,' in l:
        l=l.replace('dereferenceable(7) %target.i.sroa.0,','dereferenceable(7) %target.sroa.0,',1); n+=1
    out.append(l)
assert n>=2 and m==1,(n,m)
open(sys.argv[2],'w').write('\n'.join(out))
