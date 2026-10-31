#!/usr/bin/env python3
"""shiftmap.py [cand.so|m.o] [--k 1,2,3] [--top 15] (experiment only)
Positional-slot value of a pure, size-neutral shift in admin_cto::execute (0x22a10).
Model: insert k junk 8-byte slots at ours slot p and delete k slots at ours slot q (q>p; or the reverse for k<0), so ours
[p,q) moves by k slots and everything else stays. slots_diff is positional, so the gain is
  new_matches - old_matches = (P_k[q+k]-P_k[p+k]) - (P_0[q+k]-P_0[p]),  P_k = prefix sum of [orig[j]==ours[j-k]].
It ignores the cost of the inserted/deleted instructions themselves (SequenceMatcher M is shift-invariant to first order),
so it is the slot ceiling of pairing a +8k B change at p with a -8k B change at q, e.g. two size knobs.
Masking: call imm/src and lddw imms masked, like target_metric. Default candidate: current baseline unstripped.so."""
import sys,os,struct,re
H=os.environ.get('HARNESS','/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness')
sys.path.insert(0,H)
from score import original_windows
KEEP=r'admin_cto7execute'
def elf_fn(path,pat):
    b=open(path,'rb').read()
    shoff=struct.unpack_from('<Q',b,0x28)[0]; shentsize,shnum,shstrndx=struct.unpack_from('<HHH',b,0x3a)
    sh=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*shentsize) for i in range(shnum)]
    for s in sh:
        if s[1]==2:
            so=sh[s[6]][4]
            for j in range(s[5]//24):
                nm,info,oth,shndx,val,size=struct.unpack_from('<IBBHQQ',b,s[4]+j*24)
                name=b[so+nm:b.index(b'\0',so+nm)].decode()
                if re.search(pat,name) and (info&0xf)==2:
                    sec=sh[shndx]; off=sec[4]+val-(sec[3] if path.endswith('.so') else 0)
                    return b[off:off+size]
def mask(raw):
    m=bytearray(raw); i=0
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8
        if op==0x85: m[i+1]&=0x0f; m[i+4:i+8]=b'\0'*4
        if op==0x18: m[i+4:i+8]=b'\0'*4; m[i+12:i+16]=b'\0'*4
        i+=n
    return bytes(m)
a=sys.argv[1:]; cand=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
ks=[1,2,3]; top=15
while a:
    x=a.pop(0)
    if x=='--k': ks=[int(v) for v in a.pop(0).split(',')]
    elif x=='--top': top=int(a.pop(0))
    else: cand=x
o=mask([w for w in original_windows() if w['start']==0x22a10][0]['raw']); c=mask(elf_fn(cand,KEEP))
n=len(o)//8; assert len(c)==len(o),'sizes differ'
O=[o[8*i:8*i+8] for i in range(n)]; Cc=[c[8*i:8*i+8] for i in range(n)]
def P(k):
    p=[0]*(n+1)
    for j in range(n):
        i=j-k; p[j+1]=p[j]+(1 if 0<=i<n and O[j]==Cc[i] else 0)
    return p
P0=P(0); base=n-P0[n]
print('candidate',cand,'slots_diff',base)
for k in ks+[-x for x in ks]:
    Pk=P(k); lo=max(0,-k); hi=min(n,n-k)
    A=lambda x:Pk[x+k]-P0[x+k]   # end term (delete position q)
    B=lambda x:Pk[x+k]-P0[x]     # start term (insert position p); gain(p,q)=A(q)-B(p), p<q
    best=None; minB=None; arg=None
    for q in range(lo,hi+1):
        if minB is not None and (best is None or A(q)-minB>best[0]): best=(A(q)-minB,arg,q)
        if q<hi and (minB is None or B(q)<minB): minB=B(q); arg=q
    g,p,q=best
    print('k=%+d best gain %d slots: insert at ours 0x%x, delete at ours 0x%x'%(k,g,p*8,q*8))
    grid=[]
    for p0 in range(lo,hi,16):
        bq=max((A(q)-B(p0),q) for q in range(p0+1,hi+1,16)); grid.append((bq[0],p0,bq[1]))
    grid.sort(reverse=True); seen=[]
    for g2,p0,q0 in grid:
        if any(abs(p0-x)<128 for x in seen): continue
        seen.append(p0); print('   gain %4d  p=0x%05x q=0x%05x'%(g2,p0*8,q0*8))
        if len(seen)>=max(1,top//3): break
