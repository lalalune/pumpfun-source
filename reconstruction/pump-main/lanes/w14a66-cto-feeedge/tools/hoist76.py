#!/usr/bin/env python3
"""hoist.py in.ll out.ll [mode]: write target pieces straight into target.sroa.0/.8 in validate's arms (bb44.i, bb45.i)
and drop bb76's merge memcpys so bb76 = {lifetimes, br shared} (tail-dup candidate). Oracle only."""
import sys,re
src,dst=sys.argv[1:3]; mode=sys.argv[3] if len(sys.argv)>3 else 'both'
t=open(src).read()
def blk(name):
    k=t.index('\n'+name+':'); e=t.index('\n\n',k+1); return k,e
for b in ('bb44.i','bb45.i'):
    k,e=blk(b); x=t[k:e]
    x=x.replace('dereferenceable(7) %target.i.sroa.0,','dereferenceable(7) %target.sroa.0,',1)
    if mode=='both': x=x.replace('dereferenceable(9) %target.i.sroa.9,','dereferenceable(9) %target.sroa.8,',1)
    t=t[:k]+x+t[e:]
k,e=blk('bb76'); x=t[k:e]; L=x.split('\n')
L=[l for l in L if not ('memcpy' in l and ('%target.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %target.i.sroa.0' in l or (mode=='both' and ('%_48.sroa.11, ptr' in l or '%target.sroa.8, ptr noundef nonnull align 8 dereferenceable(9) %_48.sroa.11' in l))))]
t=t[:k]+'\n'.join(L)+t[e:]
open(dst,'w').write(t)
