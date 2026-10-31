#!/usr/bin/env python3
"""sdiff.py a.bin b.bin [minrun]: skeleton (regs/frame/jumps masked) diff of two candidates; list insert/delete runs with offsets."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle,xled
_a=sys.argv; sys.argv=["x"]; from fr import fm,rm,jm; sys.argv=_a
def load(p): return oracle.mask(oracle.orig_window() if p=="orig" else xled.load(p))
a=load(sys.argv[1]); b=load(sys.argv[2]); mr=int(sys.argv[3]) if len(sys.argv)>3 else 4
def offs(t):
    o=[0];
    for x in t: o.append(o[-1]+len(x))
    return o
oa,ob=offs(a),offs(b)
sa=jm(rm(fm(a))); sb=jm(rm(fm(b)))
sm=difflib.SequenceMatcher(None,sa,sb,autojunk=False)
tot={'delete':0,'insert':0,'replace':0}
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    tot[tag]+=max(i2-i1,j2-j1)
    if max(i2-i1,j2-j1)>=mr: print(f'{tag:8s} a[{oa[i1]:#x}..{oa[i2]:#x}) {i2-i1:4d}  b[{ob[j1]:#x}..{ob[j2]:#x}) {j2-j1:4d}')
print('M',sum(k.size for k in sm.get_matching_blocks()),tot)
