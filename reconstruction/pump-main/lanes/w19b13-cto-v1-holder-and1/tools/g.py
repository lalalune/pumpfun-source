#!/usr/bin/env python3
"""g.py <name> <gene+gene+...>: apply text genes to the worktree's admin_cto.rs and write $OUT/src/<name>.rs"""
import sys,os,re
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w19b13-cto-v1-holder-and1'
G={}
def gene(n,*pairs): G[n]=pairs
exec(open(OUT+'/tools/genes.py').read())
def apply(names,src):
    for n in names:
        if n=='d312':
            src=_d312(src); continue
        for a,b in G[n]:
            assert a in src,(n,a[:120])
            src=src.replace(a,b)
    return src
if __name__=='__main__':
    name=sys.argv[1]; genes=sys.argv[2].split('+') if len(sys.argv)>2 and sys.argv[2] else []
    s=open(OUT+'/src/base.rs').read()
    n0=s.count('\n')
    s=apply(genes,s)
    assert s.count('\n')==n0
    os.makedirs(OUT+'/src',exist_ok=True)
    open(f'{OUT}/src/{name}.rs','w').write(s)
