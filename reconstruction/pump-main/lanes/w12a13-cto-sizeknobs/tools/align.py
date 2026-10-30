#!/usr/bin/env python3
"""align.py <unstripped.so> : difflib opcodes between original admin_cto window and candidate, byte deltas per block."""
import sys, difflib, re
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a13-cto-sizeknobs/reconstruction/harness'
sys.path.insert(0,H)
from score import original_windows
from win import Cand, insns, demangle, ORIG_SECS
so=sys.argv[1]
W=[w for w in original_windows() if w['start']==0x22a10][0]
c=Cand(so)
pick=[(s,n,nm) for s,n,nm in c.funcs if re.search(r'admin_cto::execute$',demangle(nm))][0]
s,n,nm=pick
o=insns(W['raw'],W['start'],ORIG_SECS); k=insns(c.fn(s,n),s,c.secs)
ot=[x[2] for x in o]; kt=[x[2] for x in k]
sm=difflib.SequenceMatcher(None,ot,kt,autojunk=False)
print('ratio',round(sm.ratio(),5),'orig',W['bytes'],'cand',n)
tot=0
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    ob=sum(len(x[1]) for x in o[i1:i2]); cb=sum(len(x[1]) for x in k[j1:j2])
    tot+=cb-ob
    if abs(cb-ob)>=8 or '-v' in sys.argv:
        print(f'{tag:7s} orig {i1:5d}-{i2:5d} (+0x{o[i1][0]-W["start"] if i1<len(o) else 0:05x}) {ob:5d}B  cand {j1:5d}-{j2:5d} {cb:5d}B  delta {cb-ob:+d}  cum {tot:+d}')
