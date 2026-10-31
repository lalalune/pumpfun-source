#!/usr/bin/env python3
"""splice.py <cand.so> <olo> <ohi> <clo> <chi>: ratio of cand window after replacing cand[clo,chi) with orig[olo,ohi) (bound, what-if only)."""
import sys,runpy,os
sys.argv_save=sys.argv[:]
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness'
sys.path.insert(0,H)
import importlib.util
src=open(os.path.join(os.path.dirname(__file__),'rx.py')).read()
pre=src[:src.index("OUT=os.environ")]
g={}; exec(pre,g)
so,olo,ohi,clo,chi=sys.argv_save[1],*[int(x,16) for x in sys.argv_save[2:6]]
cand=g['elf_fn'](so,g['KEEP']); orig=g['orig_window']()
r0,s0=g['metric'](cand,orig)
c2=cand[:clo]+orig[olo:ohi]+cand[chi:]
r1,s1=g['metric'](c2,orig)
print('base %.5f %s  spliced %.5f %s  delta %+.5f'%(r0,s0,r1,s1,r1-r0))
