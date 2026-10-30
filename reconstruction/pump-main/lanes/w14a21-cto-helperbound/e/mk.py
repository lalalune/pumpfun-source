#!/usr/bin/env python3
"""mk.py name spec: spec = '+'-joined genes (hb.py G names or pool P names); writes src_edits/<name>.py against current WT source."""
import sys,os,runpy
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a21-cto-helperbound')
SRC='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a21-cto-helperbound/programs/pump/src/creator/admin_cto.rs'
sys.argv=[sys.argv[0],SRC,'__none__']+sys.argv[1:]
name,spec=sys.argv[3],sys.argv[4]
sys.path.insert(0,O+'/e'); import pool
hb=runpy.run_path(O+'/e/hb.py',run_name='hb')
src=open(SRC).read(); E=[]; s=src
for g in spec.split('+'):
    e=hb['G'][g] if g in hb['G'] else pool.P[g]
    r=pool.apply(s,e); assert r is not None,(g,'does not apply'); assert r!=s,(g,'no-op')
    s=r; E+=e
open(f'{O}/src_edits/{name}.py','w').write('EDITS='+repr(E)+'\n'); print('ok',name)
