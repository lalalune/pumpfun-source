#!/usr/bin/env python3
"""gen.py <prefix> <basespec> <gene-prefix-filter> [--out names.txt]: for every pool/hb gene matching filter, write src_edits/<prefix>.<gene>.py = base+gene if it applies, changes text and keeps newlines; dedupe by resulting text."""
import sys,os,runpy,hashlib
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a42-cto-levy1port')
SRC='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a42-cto-levy1port/programs/pump/src/creator/admin_cto.rs'
pre,base,flt=sys.argv[1:4]
sys.argv=[sys.argv[0],SRC,'__none__']
sys.path.insert(0,O+'/e'); import pool
hb=runpy.run_path(O+'/e/hb.py',run_name='hb')
src=open(SRC).read()
def G(g): return hb['G'][g] if g in hb['G'] else pool.P[g]
s=src;E=[]
for g in base.split('+'):
    r=pool.apply(s,G(g)); assert r and r!=s,g; s=r;E+=G(g)
seen=set();names=[]
for g in sorted(set(list(pool.P)+list(hb['G']))):
    if not any(g.startswith(f) for f in flt.split(',')): continue
    try: e=G(g)
    except Exception: continue
    if not isinstance(e,list): continue
    r=pool.apply(s,e)
    if r is None or r==s: continue
    h=hashlib.md5(r.encode()).hexdigest()
    if h in seen: continue
    seen.add(h); n=f'{pre}.{g}'; open(f'{O}/src_edits/{n}.py','w').write('EDITS='+repr(E+e)+'\n'); names.append(n)
print(' '.join(names))
