#!/usr/bin/env python3
"""fpairs.py <so> lo hi: for frame-masked matched instrs in orig range, histogram of (orig r10 off - cand r10 off)."""
import sys,difflib,collections,struct
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a37-cto-skelregress/reconstruction/harness')
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a37-cto-skelregress/tools')
import ctoracle as C, win
from score import original_windows
so=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
w=next(w for w in original_windows() if w['start']==0x22a10)
oi=win.insns(w['raw'],w['start'],win.ORIG_SECS)
c=win.Cand(so); s,n,nm=next((s,n,nm) for s,n,nm in c.funcs if win.demangle(nm).endswith('admin_cto::execute'))
ci=win.insns(c.fn(s,n),s,c.secs)
sm=difflib.SequenceMatcher(None,[C.abstract(x[2]) for x in oi],[C.abstract(x[2]) for x in ci],autojunk=False)
H=collections.Counter(); P=[]
def r10off(t):
    op=t[0]; regs=t[1]; dst=regs&15; src=regs>>4; off=struct.unpack('<h',t[2:4])[0]
    if (op&7) in (1,) and src==10: return off   # ldx
    if (op&7) in (2,3) and dst==10: return off  # st/stx
    if op==0x07 and dst!=10: pass
    return None
for a,b,k in sm.get_matching_blocks():
    for i in range(k):
        oa=oi[a+i][0]-w['start']
        if not(lo<=oa<hi): continue
        to=oi[a+i][2]; tc=ci[b+i][2]
        if to==tc: continue
        ro=r10off(to); rc=r10off(tc)
        if ro is not None and rc is not None:
            H[ro-rc]+=1; P.append((hex(oa),hex(-ro),hex(-rc)))
        else: H['other']+=1
print(H.most_common(15))
if len(sys.argv)>4:
    for p in P: print(*p)
