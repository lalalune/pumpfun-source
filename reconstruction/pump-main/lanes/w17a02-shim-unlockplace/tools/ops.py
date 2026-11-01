#!/usr/bin/env python3
# ops.py <unstripped.so> [lo hi]: difflib opcodes of admin_cto vs original; prints orig-only / cand-only runs (orig offset range lo..hi)
import sys,re,difflib
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a02-shim-unlockplace/reconstruction/harness'
sys.path.insert(0,H)
from score import original_windows
from win import Cand, insns, demangle, ORIG_SECS
W=[w for w in original_windows() if w['start']==0x22a10][0]
O=insns(W['raw'],W['start'],ORIG_SECS); otok=[x[2] for x in O]
p=sys.argv[1]; lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 1<<30
c=Cand(p); s,n,nm=[(s,n,nm) for s,n,nm in c.funcs if re.search(r'admin_cto::execute$',demangle(nm))][0]
C=insns(c.fn(s,n),s,c.secs); ctok=[x[2] for x in C]
sm=difflib.SequenceMatcher(None,otok,ctok,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    oo=O[i1][0]-W['start'] if i1<len(O) else -1
    if not (lo<=oo<hi): continue
    co=C[j1][0]-s if j1<len(C) else -1
    print(f"{tag:8s} orig {oo:#06x} n{i2-i1:<4d} cand {co:#06x} n{j2-j1}")
    if '-v' in sys.argv:
        for k in range(i1,min(i2,i1+12)): print('   -',otok[k])
        for k in range(j1,min(j2,j1+12)): print('   +',ctok[k])
