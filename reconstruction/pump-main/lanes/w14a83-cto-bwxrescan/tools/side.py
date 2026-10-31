#!/usr/bin/env python3
"""side.py fn.bin lo hi: plain-alignment opcodes for orig window offsets [lo,hi): matched runs summarized, misses listed"""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__)); import bwx, dis as D
o=bwx.orig_toks(); c=open(sys.argv[1],'rb').read(); lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness')
from score import original_windows
ow=[w for w in original_windows() if w['start']==0x22a10][0]['raw']
od=D.dis(ow); cd=D.dis(c)
cm=bwx.mask(c)
sm=difflib.SequenceMatcher(None,o,cm,autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if od[min(i1,len(od)-1)][0]>=hi or (i2<len(od) and od[i2][0]<lo): continue
    if op=='equal': print(f'  = {i2-i1} insns  orig {od[i1][0]:#x} cand {cd[j1][0]:#x}'); continue
    n=max(i2-i1,j2-j1)
    for k in range(n):
        a=od[i1+k] if i1+k<i2 else None; b=cd[j1+k] if j1+k<j2 else None
        print(f"{op[0]} {(hex(a[0])+' '+a[1]) if a else '':42} | {(hex(b[0])+' '+b[1]) if b else ''}")
