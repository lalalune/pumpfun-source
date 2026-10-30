#!/usr/bin/env python3
"""cdiff.py <a.so> <b.so> [--sym RE]: diff admin_cto::execute between two candidate builds (normalized tokens, objdump text)."""
import sys, re, difflib, subprocess
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a13-cto-sizeknobs/reconstruction/harness'
sys.path.insert(0,H)
from win import Cand, insns, demangle, objdump_text
sym=r'admin_cto::execute$'
def load(p):
    c=Cand(p)
    s,n,nm=[(s,n,nm) for s,n,nm in c.funcs if re.search(sym,demangle(nm))][0]
    ins=insns(c.fn(s,n),s,c.secs)
    txt=objdump_text(p,s,s+n)
    return [(a-s, tok, re.sub(r'<[^>]+>','',txt.get(a,'?'))) for a,_,tok in ins]
A=load(sys.argv[1]); B=load(sys.argv[2])
sm=difflib.SequenceMatcher(None,[x[1] for x in A],[x[1] for x in B],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    print(f'== {tag} a[{i1}:{i2}] +0x{A[i1][0] if i1<len(A) else 0:x}  b[{j1}:{j2}] +0x{B[j1][0] if j1<len(B) else 0:x}')
    for x in A[i1:i2][:12]: print('  -', f'+0x{x[0]:05x}', x[2])
    for x in B[j1:j2][:12]: print('  +', f'+0x{x[0]:05x}', x[2])
