#!/usr/bin/env python3
"""cause.py <cand> [hi]: classify orig-only true-LCS (rfj) tokens in orig [0,hi) by source cause."""
import sys,os,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
import dis as D
from lcschunk_m import matched_ops
p=sys.argv[1]; hi=int(sys.argv[2],16) if len(sys.argv)>2 else 0x1800
O=oracle.orig_window(); ot,oo=xled.toks(O)
C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'); ct,co=xled.toks(C)
f=mk(1,1,1); ops=matched_ops(f(ot),f(ct)); dO=dict(D.d(O)); dC=dict(D.d(C))
def cls(a,s):
    if 0x80<=a<0x148: return 'A head: holder-rewards PDA before shared (PDA-first)'
    if 0x288<=a<0x2b8 or a in (0x150,0x210,0x258,0x268): return 'B head: curve bools / held ptrs loaded early (flaghoist, held r8/r9)'
    if re.match(r'stw \[r10-0x(238|2b8)\]',s): return 'C error code/line imm: error-block order (B/Br)'
    if 0x1258<=a<0x1378: return 'D 307/312 to_string outlined'
    if 0x4d0<=a<0x540 or 0xc08<=a<0xc60 or 0x1138<=a<0x1180 or 0x1850<=a<0x1898: return 'E new entry copy (1/7/8/8/8/1 SROA pieces)'
    if re.match(r'mov64 r\d, -?\d+$',s) or re.search(r'\[r10-0x9(50|58)\]',s) or 'stxdw [r10-0x8f8]' in s: return 'F per-arm phi constants (holder/skip/collect_old)'
    if 0x420<=a<0x4d0: return 'G CtoState store order'
    if s.startswith(('ja','jeq','jne','jlt','jgt')): return 'H branch layout / threading'
    if s.startswith(('ldxdw r','stxdw [r10','ldxb','ldxw','stxw','stxb')): return 'I copies / spill-reload placement'
    return 'J other ISel ('+s.split()[0]+')'
agg={}; ours=0
for op,i,j in ops:
    if op=='-' and oo[i]<hi:
        c=cls(oo[i],dO[oo[i]]); agg.setdefault(c,[]).append(oo[i])
    if op=='+' and j is not None: pass
tot=sum(len(v) for v in agg.values()); print(f'orig-only rfj tokens in [0,{hi:#x}): {tot}')
for c in sorted(agg): v=agg[c]; print(f'{len(v):4d}  {c}   [{" ".join(f"{x:x}" for x in v[:12])}{" ..." if len(v)>12 else ""}]')
