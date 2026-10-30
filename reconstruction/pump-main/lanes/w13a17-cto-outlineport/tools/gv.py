#!/usr/bin/env python3
"""gv.py <name> <base:main|z1|varname> gene... : make OUT/var/<name> from base crate with genes applied (line count kept)."""
import sys,os,subprocess
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a17-cto-outlineport'
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a17-cto-outlineport'
sys.path.insert(0,OUT+'/tools'); from genes import E
name,base=sys.argv[1],sys.argv[2]; genes=sys.argv[3:]
src=f'{WT}/programs/pump/' if base=='main' else f'{OUT}/var/{base}/'
d=f'{OUT}/var/{name}'; os.makedirs(d,exist_ok=True)
subprocess.check_call(['rsync','-a','--delete','--exclude','target',src,d+'/'])
p=f'{d}/src/creator/admin_cto.rs'; s=open(p).read(); s0=s
for g in genes:
    for a,b in E[g]:
        c=s.count(a)
        if c!=1: raise SystemExit(f'gene {g}: count {c}: {a[:100]!r}')
        s=s.replace(a,b)
assert s.count('\n')==s0.count('\n'),'line count changed'
open(p,'w').write(s); print(d)
