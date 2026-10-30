#!/usr/bin/env python3
# slotb.py so... : per-0x800 bucket differing normalized slots (equal-size only)
import sys
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/y1-cto-diffwin/reconstruction/harness')
from score import original_windows, normalize
from win import Cand
W=[w for w in original_windows() if w['start']==0x22a10][0]
B=0x800; nb=(W['bytes']+B-1)//B
print('bucket   '+' '.join(f'{i*B:>5x}' for i in range(nb)))
for p in sys.argv[1:]:
    c=Cand(p); s,n,nm=[x for x in c.funcs if 'admin_cto7execute' in x[2]][0]
    name=p.split('/')[-2].replace('out-','')
    if n!=W['bytes']: print(f'{name[:10]:10} size {n}'); continue
    nm_=normalize(c.fn(s,n),s,c.secs)
    d=[0]*nb
    for i in range(0,n,8):
        if nm_[i:i+8]!=W['norm'][i:i+8]: d[i//B]+=1
    print(f'{name[:10]:10} '+' '.join(f'{x:>5}' for x in d)+f'  sum {sum(d)}')
