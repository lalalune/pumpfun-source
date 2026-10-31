#!/usr/bin/env python3
"""irmove.py in.ll out.ll FIRST LAST BEFORE: in an instnamer'd module, move the IR blocks FIRST..LAST (text order, inclusive)
of execute so they sit right before block BEFORE. ISel follows IR order, so on BPF this changes which block every
conditional-branch block is glued to (experiment only)."""
import sys,re
src,dst,f,l,bef=sys.argv[1:6]; L=open(src).read().split('\n')
def start(nm): 
    for i,x in enumerate(L):
        if re.match(r'^'+re.escape(nm)+r':',x): return i
    raise SystemExit('no '+nm)
a=start(f); e=start(l); k=e+1
while not re.match(r'^[A-Za-z0-9_."$]+:',L[k]) and L[k]!='}': k+=1
blk=L[a:k]; rest=L[:a]+L[k:]
t=[i for i,x in enumerate(rest) if re.match(r'^'+re.escape(bef)+r':',x)][0]
open(dst,'w').write('\n'.join(rest[:t]+blk+rest[t:]))
