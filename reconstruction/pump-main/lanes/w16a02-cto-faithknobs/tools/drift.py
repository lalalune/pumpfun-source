#!/usr/bin/env python3
"""drift.py <fn.bin|unstripped.so> [--bins]: w16-strategy ceilings decomp.py --drift on a raw-IR oracle fn.bin (experiment only).
Prints M (exact masked difflib), true LCS under full mask (frame+reg+jmp), the jump-displacement mismatch count among
jumps aligned under mask_jmp, and the region drift (ours-orig tokens along the full-mask LCS) for the four regions the
w16 brief uses: entry (orig <0x200), validate tail (orig 0x1000-0x1800), sharing-CPI build (orig 0x3c00-0x4a80) and
event/error (orig >= 0x4a80). With --bins it prints the per-0x200 drift table."""
import sys,os,struct,difflib
import numpy as np
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from oracle import mask,orig_window,elf_fn,KEEP
p=sys.argv[1]
raw=elf_fn(p,KEEP) if p.endswith('.so') else open(p,'rb').read()
OT=mask(orig_window()); CT=mask(raw)
JMP={0x05,0x15,0x1d,0x25,0x2d,0x35,0x3d,0x45,0x4d,0x55,0x5d,0x65,0x6d,0x75,0x7d,0xa5,0xad,0xb5,0xbd,0xc5,0xcd,0xd5,0xdd}
def fields(t):
    return t[0],t[1]&15,t[1]>>4,struct.unpack_from('<h',t,2)[0],struct.unpack_from('<i',t,4)[0]
def is_frame(t):
    op,d,s,o,i=fields(t); c=op&7
    return (c==1 and s==10) or (c in (2,3) and d==10)
def abstract(toks,mf=False,mr=False,mj=False):
    out=[];prev=None
    for t in toks:
        op,d,s,o,i=fields(t); rest=bytes(t[8:])
        if mf and is_frame(t): o='F'
        if mf and prev is not None and t[0]==0x07 and prev[0]==0xbf and fields(prev)[2]==10 and fields(prev)[1]==d: i='F'
        if mj and op in JMP: o='J'
        if mr:
            d='R' if d!=10 else 10; s='R' if s!=10 else 10
        out.append((op,d,s,o,i,rest)); prev=t
    return out
def lcs(A,B):
    v={}; a=np.array([v.setdefault(x,len(v)) for x in A],dtype=np.int32); b=np.array([v.setdefault(x,len(v)) for x in B],dtype=np.int32)
    n,m=len(a),len(b); dp=np.zeros((n+1,m+1),dtype=np.int16)
    for i in range(1,n+1):
        eq=(b==a[i-1]).astype(np.int16); pr=dp[i-1]; dp[i,1:]=np.maximum.accumulate(np.maximum(pr[1:],pr[:-1]+eq))
    i,j=n,m; pairs=[]
    while i>0 and j>0:
        if a[i-1]==b[j-1] and dp[i,j]==dp[i-1,j-1]+1: pairs.append((i-1,j-1)); i-=1; j-=1
        elif dp[i-1,j]>=dp[i,j-1]: i-=1
        else: j-=1
    return int(dp[n,m]),pairs[::-1]
oo=[];o=0
for t in OT: oo.append(o); o+=len(t)
M=sum(x.size for x in difflib.SequenceMatcher(None,OT,CT,autojunk=False).get_matching_blocks())
L,pairs=lcs(abstract(OT,True,True,True),abstract(CT,True,True,True))
L2,pairs2=lcs(abstract(OT,mj=True),abstract(CT,mj=True))
nj=sum(1 for i,j in pairs2 if OT[i][0] in JMP); nbad=sum(1 for i,j in pairs2 if OT[i][0] in JMP and OT[i]!=CT[j])
def reg(lo,hi):
    ds=[j-i for i,j in pairs if lo<=oo[i]<hi]
    return sorted(ds)[len(ds)//2] if ds else None
R={'entry':reg(0,0x200),'validate_tail':reg(0x1000,0x1800),'sharecpi':reg(0x3c00,0x4a80),'event_err':reg(0x4a80,0x7000)}
import json
print(json.dumps({'bytes':len(raw),'M':M,'rfj_lcs':L,'j_lcs':L2,'jumps_aligned':nj,'jumps_bad':nbad,'drift_med':R}))
if '--bins' in sys.argv:
    bins={}
    for i,j in pairs: bins.setdefault(oo[i]//0x200*0x200,[]).append(j-i)
    for b in sorted(bins):
        ds=bins[b]; print(f'{b:#07x} {sorted(ds)[len(ds)//2]:+5d}  n={len(ds)}')
