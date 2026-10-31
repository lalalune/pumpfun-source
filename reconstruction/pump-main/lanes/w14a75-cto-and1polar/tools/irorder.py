#!/usr/bin/env python3
"""irorder.py <m.ll> <out.ll> <block>[..<lastblock>] <before-block>: post-opt IR block-ORDER oracle (experiment only).
Moves the IR block (or the contiguous run block..lastblock) of the slimmed post-opt module so it sits just before
<before-block>, then run tools/px.py on <out.ll>. On BPF, analyzeBranch cannot analyze conditional branches, so
MachineBlockPlacement keeps ISel's fallthrough, and ISel falls through to the NEXT IR block when it is a successor:
the IR block order fixes the polarity/fallthrough of every conditional-branch block. Only named (non-numbered)
blocks can be moved without renumbering (use w14a39 renum.py otherwise)."""
import sys,re
src,dst,spec,before=sys.argv[1:5]
L=open(src).read().split('\n')
def lab(l):
    m=re.match(r'^("[^"]+"|[\w.$-]+):',l); return m.group(1).strip('"') if m else None
starts=[i for i,l in enumerate(L) if lab(l)]
def span(a,b):
    s=[i for i in starts if lab(L[i])==a][0]; e0=[i for i in starts if lab(L[i])==b][0]
    nxt=[i for i in starts if i>e0]; e=nxt[0] if nxt else None
    if e is None or L[e-1].strip()=='}': e=e0+[k for k,l in enumerate(L[e0:]) if l=='}'][0]
    return s,e
a,b=(spec.split('..')+[None])[:2]; s,e=span(a,b or a)
c=L[s:e]; rest=L[:s]+L[e:]
k=[i for i,l in enumerate(rest) if lab(l)==before][0]
open(dst,'w').write('\n'.join(rest[:k]+c+rest[k:]))
