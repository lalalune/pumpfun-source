#!/usr/bin/env python3
"""skdiff.py <so> [lo hi] : skeleton (regs+frame+jumps masked) diff vs original, opcodes overlapping orig offset range [lo,hi)."""
import sys,difflib
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a37-cto-skelregress/reconstruction/harness')
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a37-cto-skelregress/tools')
import ctoracle as C, win
from score import original_windows
so=sys.argv[1]; lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 27400
w=next(w for w in original_windows() if w['start']==0x22a10)
oi=win.insns(w['raw'],w['start'],win.ORIG_SECS)
ot=win.objdump_text(win.resolve_original(win.BASE/'original.so'),w['start'],w['start']+w['bytes'])
c=win.Cand(so); s,n,nm=next((s,n,nm) for s,n,nm in c.funcs if win.demangle(nm).endswith('admin_cto::execute'))
ci=win.insns(c.fn(s,n),s,c.secs); ct=c.disassembly(s,n)
def sk(t): b=bytearray(C.abstract(t)); b[1]=0; return bytes(b)
sm=difflib.SequenceMatcher(None,[sk(x[2]) for x in oi],[sk(x[2]) for x in ci],autojunk=False)
for tag,a1,a2,b1,b2 in sm.get_opcodes():
    if tag=='equal': continue
    oa=oi[a1][0]-w['start'] if a1<len(oi) else 27400
    if not (lo<=oa<hi): continue
    print(f'== {tag} orig {oa:#x}+{a2-a1}  cand {(ci[b1][0]-s) if b1<len(ci) else n:#x}+{b2-b1}')
    for x in oi[a1:a2][:30]: print(f'  - {x[0]-w["start"]:#06x} {ot.get(x[0],"?")}')
    for x in ci[b1:b2][:30]: print(f'  + {x[0]-s:#06x} {ct.get(x[0],"?")}')
