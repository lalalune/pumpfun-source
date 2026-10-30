#!/usr/bin/env python3
"""region.py <cand.so>: per-region (N equal byte ranges of the original window) diff counts.
For each region: original instruction count, how many are matched by a global difflib alignment
(strict: call/lddw imm masked; loose: also regs and stack offsets masked)."""
import sys,re,difflib,argparse
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w10r1-admincto-region1of6/tools')
from sdis import dis
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w10r1-admincto-region1of6/reconstruction/harness')
from score import BASE
from original_input import resolve_original
from elf_symbols import function_symbols
def strict(t):
    t=re.sub(r'^call -?0x[0-9a-f]+','call X',t)
    t=re.sub(r'^(lddw r\d+), 0x[0-9a-f]+',r'\1, X',t)
    if t.startswith('j'): t=re.sub(r'[+-]0x[0-9a-f]+$','J',t)
    return t
def loose(t):
    t=strict(t); t=re.sub(r'r\d+','r',t); t=re.sub(r'\[r [+-] 0x[0-9a-f]+\]','[m]',t); return t
def rdemangle(s): return s
ap=argparse.ArgumentParser();ap.add_argument('so');ap.add_argument('--n',type=int,default=6);ap.add_argument('--show',type=int,default=0,help='print aligned diff of region K (1-based)')
ap.add_argument('--mode',default='loose');ap.add_argument('--dis',help='candidate disassembly text file (off text) instead of so')
a=ap.parse_args()
OS,ON=0x22a10,27400
o=dis(resolve_original(BASE/'original.so'),OS,ON)
if a.dis:
    c=[]
    for l in open(a.dis):
        x,t=l.rstrip('\n').split(None,1); c.append((int(x,16),t.strip()))
    cn=c[-1][0]+8
else:
    blob=open(a.so,'rb').read()
    cand=[f for f in function_symbols(blob) if re.search(r'9admin_cto7execute17h',f[2])]
    assert len(cand)==1,cand
    cs,cn,_=cand[0]
    c=dis(a.so,cs,cn)
res={}
for mode,fn in (('strict',strict),('loose',loose)):
    ot=[fn(t) for _,t in o]; ct=[fn(t) for _,t in c]
    sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
    matched=[False]*len(ot)
    for i,j,n in sm.get_matching_blocks():
        for k in range(i,i+n): matched[k]=True
    regs=[]
    for r in range(a.n):
        lo,hi=ON*r//a.n,ON*(r+1)//a.n
        idx=[k for k,(off,_) in enumerate(o) if lo<=off<hi]
        regs.append((len(idx),sum(matched[k] for k in idx)))
    res[mode]=(sm.ratio(),regs)
    if a.show and mode==a.mode:
        lo,hi=ON*(a.show-1)//a.n,ON*a.show//a.n
        for tag,i1,i2,j1,j2 in sm.get_opcodes():
            if i2<=0: continue
            if not any(lo<=o[k][0]<hi for k in range(i1,i2)) and not (i1<len(o) and lo<=o[min(i1,len(o)-1)][0]<hi): continue
            if tag=='equal': print(f'  = {i2-i1} ({o[i1][0]:#06x}..) <-> cand {c[j1][0]:#06x}..'); continue
            for k in range(i1,i2): print(f'- {o[k][0]:#06x} {o[k][1]}')
            for k in range(j1,j2): print(f'+ {c[k][0]:#06x} {c[k][1]}')
print(f'cand_bytes {cn}')
hi=ON//a.n
for mode,fn in (('strict',strict),('loose',loose)):
    ot=[fn(t) for off,t in o if off<hi]; ct=[fn(t) for off,t in c if off<hi*1.3]
    sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
    print(f'R1local-{mode} {sum(n for _,_,n in sm.get_matching_blocks())}/{len(ot)}')
for mode,(ratio,regs) in res.items():
    print(mode, f'ratio={ratio:.4f}', ' '.join(f'R{i+1}:{m}/{n}' for i,(n,m) in enumerate(regs)))
