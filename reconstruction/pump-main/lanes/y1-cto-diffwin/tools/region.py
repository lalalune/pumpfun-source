#!/usr/bin/env python3
# region.py so... : per-0x800 orig bucket matched-instruction counts for admin_cto (0x22a10)
import sys,difflib,re
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/y1-cto-diffwin/reconstruction/harness')
from score import original_windows
from win import Cand, insns, ORIG_SECS, demangle
W=[w for w in original_windows() if w['start']==0x22a10][0]
oi=insns(W['raw'],W['start'],ORIG_SECS); ot=[x[2] for x in oi]
B=0x800; nb=(W['bytes']+B-1)//B
tot=[0]*nb
for a,_,_ in oi: tot[(a-W['start'])//B]+=1
print('bucket   '+' '.join(f'{i*B:>5x}' for i in range(nb)))
print('total    '+' '.join(f'{t:>5}' for t in tot))
for p in sys.argv[1:]:
    c=Cand(p); f=[x for x in c.funcs if 'admin_cto7execute' in x[2] ][0]
    s,n,nm=f
    ct=[x[2] for x in insns(c.fn(s,n),s,c.secs)]
    sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
    m=[0]*nb
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): m[(oi[blk.a+k][0]-W['start'])//B]+=1
    name=p.split('/')[-2].replace('out-','')
    print(f'{name[:8]:8} '+' '.join(f'{x:>5}' for x in m)+f'  sum {sum(m)} bytes {n} r {sm.ratio():.4f}')
