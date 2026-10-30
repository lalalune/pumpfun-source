#!/usr/bin/env python3
"""jumpmap.py <cand.so> [k_slots...]: where would inserting k slots fix (or break) aligned jump offsets vs the original?
Aligns orig/cand with jump offsets masked, then for aligned jump pairs computes d = orig_off - cand_off (slots).
For each insertion point p (cand slot index) prints the net matched-jump change for k-slot insertion, as ranges."""
import sys, re, struct, difflib
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a13-cto-sizeknobs/reconstruction/harness'
sys.path.insert(0,H)
from score import original_windows
from win import Cand, insns, demangle, ORIG_SECS

def decode(seq):
    out=[]; slot=0
    for addr,raw,norm in seq:
        op=raw[0]; cls=op&7
        isj = cls in (5,6) and op not in (0x85,0x95,0x8d)
        off=struct.unpack_from('<h',raw,2)[0]
        n=len(raw)//8
        masked = norm[:2]+b'\0\0'+norm[4:] if isj else norm
        out.append(dict(slot=slot,isj=isj,off=off,tok=norm,mtok=masked,n=n,op=op))
        slot+=n
    return out

W=[w for w in original_windows() if w['start']==0x22a10][0]
c=Cand(sys.argv[1])
s,n,nm=[(s,n,nm) for s,n,nm in c.funcs if re.search(r'admin_cto::execute$',demangle(nm))][0]
O=decode(insns(W['raw'],W['start'],ORIG_SECS)); C=decode(insns(c.fn(s,n),s,c.secs))
sm=difflib.SequenceMatcher(None,[x['mtok'] for x in O],[x['mtok'] for x in C],autojunk=False)
pairs=[]
for a,b,size in sm.get_matching_blocks():
    for t in range(size):
        o=O[a+t]; k=C[b+t]
        if k['isj']:
            pairs.append((k['slot'],k['off'],o['off']-k['off']))
from collections import Counter
print('aligned jumps',len(pairs),'d histogram',Counter(d for _,_,d in pairs).most_common(12))
total=C[-1]['slot']+C[-1]['n']
for k in [int(x) for x in sys.argv[2:]] or [1,2]:
    # net[p] for insertion before slot p
    net=[0]*(total+1)
    for slot,off,d in pairs:
        src=slot+1  # jump target = src + off
        tgt=src+off
        lo,hi=(src,tgt) if off>=0 else (tgt,src)
        # insertion at p in (lo, hi] crosses (forward: p in [src, tgt) shifting target; use src<=p<tgt)
        # forward jump: insertion before slot p with src<=p<=tgt-? -> target moves if p<=tgt and p>=src
        if off>=0: rng=(src,tgt)        # p in [src, tgt) ... insertion at p<tgt and p>=src (p=src means right after jump)
        else: rng=(tgt,slot)            # backward: insertion at p in [tgt, slot]
        delta=(1 if d==k else 0)-(1 if d==0 else 0)
        if delta==0: continue
        a,b=rng
        net[a]+=delta
        if b+1<=total: net[b+1 if off<0 else b]-=delta
    run=0; best=[]
    vals=[]
    for p in range(total+1):
        run+=net[p]; vals.append(run)
    # print ranges of best values
    mx=max(vals); mn=min(vals)
    print(f'k={k}: best net {mx} worst {mn}')
    # group contiguous ranges with value >= mx-1
    cur=None
    for p,v in enumerate(vals):
        if v>=mx-1:
            if cur and cur[1]==p-1 and cur[2]==v: cur[1]=p
            else:
                if cur: print(f'   slots {cur[0]}-{cur[1]} (+0x{cur[0]*8:x}..+0x{cur[1]*8:x}) net {cur[2]}')
                cur=[p,p,v]
    if cur: print(f'   slots {cur[0]}-{cur[1]} (+0x{cur[0]*8:x}..+0x{cur[1]*8:x}) net {cur[2]}')
