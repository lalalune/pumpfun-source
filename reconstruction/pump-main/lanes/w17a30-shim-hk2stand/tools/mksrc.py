#!/usr/bin/env python3
"""mksrc.py <out.rs> <g16 genes joined by + or -> <gx genes...>: main admin_cto.rs + w17a16 genes + w17a30 genes."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import g16,gx
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a30-shim-hk2stand'
s=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
if sys.argv[2]!='-':
    genes=[]
    for n in sys.argv[2].split('+'): genes+=g16.G[n]
    s=g16.apply(s,genes)
s=gx.apply(s,sys.argv[3:])
open(sys.argv[1],'w').write(s)
