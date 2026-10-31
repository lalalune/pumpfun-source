#!/usr/bin/env python3
"""shiftk.py <fn.bin|so> K : delete K unmatched (non-jump) instructions, as groups of size g at up to two positions,
fix crossing jumps, score M. Shows where a -8*K repay recovers the most (pure size, no other code change)."""
import sys,os,difflib,struct,bisect,multiprocessing as mp
mp=mp.get_context('fork')
sa=sys.argv[:]; sys.argv=['x','n']
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rx.py')).read().split('OUT=os.environ')[0])
p=sa[1]; K=int(sa[2]); raw=open(p,'rb').read() if p.endswith('.bin') else elf_fn(p,KEEP)
ins=[];i=0
while i<len(raw):
    n=16 if raw[i]==0x18 else 8; ins.append(bytes(raw[i:i+n])); i+=n
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
slot=[0]
for b in ins: slot.append(slot[-1]+len(b)//8)
OT=mask(orig_window())
def build(dels):
    dels=set(dels); ds=sorted(slot[d] for d in dels)
    def ns(k): return slot[k]-bisect.bisect_left(ds,slot[k])
    out=[]
    for k,b in enumerate(ins):
        if k in dels: continue
        if isj(b):
            off=struct.unpack('<h',b[2:4])[0]; t=slot[k]+1+off; ti=bisect.bisect_left(slot,t)
            nb=bytearray(b); nb[2:4]=struct.pack('<h',ns(ti)-(ns(k)+1)); b=bytes(nb)
        out.append(b)
    return b''.join(out)
def M(c):
    sm=difflib.SequenceMatcher(None,OT,mask(c),autojunk=False); return sum(x.size for x in sm.get_matching_blocks())
sm=difflib.SequenceMatcher(None,OT,mask(raw),autojunk=False); matched=set()
for b in sm.get_matching_blocks():
    for k in range(b.size): matched.add(b.b+k)
unm=[k for k in range(len(ins)) if k not in matched and not isj(ins[k]) and len(ins[k])==8]
def group(q,g):
    i=bisect.bisect_left(unm,q); return unm[i:i+g]
def ev(spec): return (spec,M(build(sum((group(q,g) for q,g in spec),[]))))
if __name__=='__main__':
    print('len',len(raw),'base M',M(raw),'unmatched',len(unm),flush=True)
    G=int(os.environ.get('GRID','256'))
    qs=[];last=-10**9
    for k in unm:
        if slot[k]*8-last>=G: qs.append(k); last=slot[k]*8
    specs=[((q,K),) for q in qs]
    with mp.Pool(int(os.environ.get('NP','4'))) as P: R=P.map(ev,specs)
    R.sort(key=lambda z:-z[1])
    print('single group of',K,':',[('%05x'%(slot[s[0][0]]*8),m) for s,m in R[:15]],flush=True)
    if K>1 and os.environ.get('TWO'):
        top=[s[0][0] for s,_ in R[:int(os.environ.get('TOP','12'))]]
        specs=[((a,g),(b,K-g)) for a in top for b in qs for g in range(1,K) if b!=a]
        with mp.Pool(int(os.environ.get('NP','4'))) as P: R2=P.map(ev,specs)
        R2.sort(key=lambda z:-z[1])
        print('two groups:',[('%05x/%d'%(slot[s[0][0]]*8,s[0][1]),'%05x/%d'%(slot[s[1][0]]*8,s[1][1]),m) for s,m in R2[:15]])
