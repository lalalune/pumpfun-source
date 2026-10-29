#!/usr/bin/env python3
"""var.py <name> <edits.py>: copy WT crate to OUT/src/<name>, apply EDITS=[(old,new),...] to create_v2.rs, keep line count."""
import sys,shutil,os,runpy
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w3-createv2/programs/pump'
L=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-createv2')
name,ed=sys.argv[1],sys.argv[2]
d=L+'/src/'+name
if os.path.exists(d): shutil.rmtree(d)
shutil.copytree(WT,d,ignore=shutil.ignore_patterns('target'))
p=d+'/src/create_v2.rs'; s=open(p).read(); n0=s.count('\n')
for a,b in runpy.run_path(ed)['EDITS']:
    assert s.count(a)==1,(s.count(a),a); s=s.replace(a,b)
assert s.count('\n')==n0,(s.count('\n'),n0)
open(p,'w').write(s); print(d)
