#!/usr/bin/env python3
"""pw.py <m.ll> <out.ll> <block>=<t|f|pNNNN>... : add !prof branch_weights to the conditional br ending each named
block of a post-opt module (t: 2000:1 true-likely, f: 1:2000, pNNNN: true prob NNNN/10000). Experiment only."""
import sys,re
src,dst=sys.argv[1],sys.argv[2]; specs=dict(x.split('=',1) for x in sys.argv[3:])
L=open(src).read().split('\n'); blk=None; extra=[]; k=0
for i,l in enumerate(L):
    m=re.match(r'^("?[\w.$-]+"?):',l)
    if m: blk=m.group(1).strip('"'); continue
    if blk in specs and re.match(r'^\s+br i1 ',l):
        s=specs[blk]
        if s=='t': w=(2000,1)
        elif s=='f': w=(1,2000)
        else: p=int(s[1:]); w=(p,10000-p)
        mid=f'!98{k:04d}'; k+=1
        L[i]=re.sub(r', !prof !\d+','',l)+f', !prof {mid}'; extra.append(f'{mid} = !{{!"branch_weights", i32 {w[0]}, i32 {w[1]}}}')
        specs.pop(blk)
assert not specs,('unmatched',specs)
open(dst,'w').write('\n'.join(L+extra)+'\n')
