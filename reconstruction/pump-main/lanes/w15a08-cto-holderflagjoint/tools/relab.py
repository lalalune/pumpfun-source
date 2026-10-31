#!/usr/bin/env python3
"""relab.py: spill-slot relabel oracle (experiment only). A permutation of a candidate's own 8 B spill-slot offsets is
always a legal colouring of the same code, so its best score bounds what any spill-colour order can give that code.
Functions: load(name) -> (bin, spillset); apply(bin,map); M(bin); bestperm(bin,spills,iters)."""
import sys,os,re,struct,difflib,json
T=os.path.dirname(os.path.abspath(__file__)); g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
ORIG=g['orig_window']()
def ins(b):
    i=0; out=[]
    while i<len(b):
        n=16 if b[i]==0x18 else 8; out.append((i,n)); i+=n
    return out
def memoff(b,i):
    op=b[i]; cls=op&7; r=b[i+1]
    if cls==1 and (r>>4)==10: return struct.unpack_from('<h',b,i+2)[0]
    if cls in(2,3) and (r&15)==10: return struct.unpack_from('<h',b,i+2)[0]
    return None
def apply(b,m):
    c=bytearray(b)
    for i,n in ins(b):
        o=memoff(b,i)
        if o is not None and o in m: struct.pack_into('<h',c,i+2,m[o])
    return bytes(c)
def M(b,ret_sm=False):
    sm=difflib.SequenceMatcher(None,g['mask'](ORIG),g['mask'](b),autojunk=False)
    m=sum(x[2] for x in sm.get_matching_blocks())
    return (m,sm) if ret_sm else m
def ratio(b): return round(difflib.SequenceMatcher(None,g['mask'](ORIG),g['mask'](b),autojunk=False).ratio(),5)
def spills(mir):
    t=open(mir).read(); st=t[t.index('\nstack:'):]
    return {int(o) for o in re.findall(r'type: spill-slot, offset: (-?\d+), size: 8',st)}
def fmask(b):
    c=bytearray(b)
    for i,n in ins(b):
        if memoff(b,i) is not None: struct.pack_into('<h',c,i+2,0)
    return bytes(c)
def votes(b,sp):
    """align frame-masked tokens of orig and cand; vote cand_off -> orig_off on aligned mem insns"""
    oi=ins(ORIG); ci=ins(b)
    sm=difflib.SequenceMatcher(None,g['mask'](fmask(ORIG)),g['mask'](fmask(b)),autojunk=False)
    V={}
    for a,c,n in sm.get_matching_blocks():
        for k in range(n):
            x=memoff(ORIG,oi[a+k][0]); y=memoff(b,ci[c+k][0])
            if x is not None and y in sp: V.setdefault(y,{}); V[y][x]=V[y].get(x,0)+1
    return V
def bestperm(b,sp,iters=3,verbose=False):
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    S=sorted(sp); cur={s:s for s in S}; best=(M(b),dict(cur))
    for it in range(iters):
        bb=apply(b,cur); V=votes(bb,set(cur.values()))
        inv={v:k for k,v in cur.items()}
        W=np.zeros((len(S),len(S)))
        idx={s:i for i,s in enumerate(S)}
        for y,d in V.items():
            src=inv[y]
            for x,w in d.items():
                if x in idx: W[idx[src],idx[x]]+=w
        # keep-current bonus tiny
        for s in S: W[idx[s],idx[cur[s]]]+=0.01
        r,c=linear_sum_assignment(-W)
        cur={S[i]:S[j] for i,j in zip(r,c)}
        m=M(apply(b,cur))
        if verbose: print('iter',it,m,file=sys.stderr)
        if m>best[0]: best=(m,dict(cur))
    return best
if __name__=='__main__':
    for d in sys.argv[1:]:
        b=g['elf_fn'](d+'/f.o',g['KEEP']); sp=spills(d+'/pei.mir')
        m0=M(b); mb,pm=bestperm(b,sp,4,True)
        print(json.dumps({'d':d,'bytes':len(b),'M':m0,'Mperm':mb,'moved':sum(1 for k,v in pm.items() if k!=v),'ratio_perm':ratio(apply(b,pm))}))
def binspills(b):
    """spill set from a binary alone: bottom-of-frame run of 8-aligned offsets accessed only as 64-bit (ldxdw/stxdw/stdw)"""
    acc={}
    for i,n in ins(b):
        o=memoff(b,i)
        if o is None: continue
        sz=(b[i]>>3)&3  # 0=W,1=H,2=B,3=DW
        acc.setdefault(o,set()).add(sz)
    offs=sorted(acc); S=set()
    # walk up from the bottom while offsets are dw-only and 8-aligned
    for o in offs:
        if o%8==0 and acc[o]=={3}: S.add(o)
        else: break
    return S
