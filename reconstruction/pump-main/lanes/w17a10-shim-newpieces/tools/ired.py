#!/usr/bin/env python3
"""ired.py <edits.py> [names...] : apply EDITS[name] (list of (old,new) exact replacements or callables) to the slim pre-opt
module and score with irbeam fx.run. Experiment only."""
import sys,os,runpy,json
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces'
os.environ['LANE_OUT']=OUT
sys.path.insert(0,OUT+'/irbeam/tools'); import fx
base=os.environ.get('BASE_LL',OUT+'/ir/m0.s.ll')
g=runpy.run_path(sys.argv[1]); V=g['V']
names=sys.argv[2:] or list(V)
t0=open(base).read()
for n in names:
    t=t0
    try:
        for e in V[n]:
            if callable(e): t=e(t); continue
            a,b=e; c=t.count(a); assert c==1,(n,c,a[:120]); t=t.replace(a,b)
    except AssertionError as ex:
        print(json.dumps({'name':n,'err':str(ex)[:300]}),flush=True); continue
    r=fx.run(t,n,keep=os.environ.get('KEEP')=='1')
    print(json.dumps(r),flush=True)
