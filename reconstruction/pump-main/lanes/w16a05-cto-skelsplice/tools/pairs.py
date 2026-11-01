#!/usr/bin/env python3
"""pairs.py <idx.npz> [--top N] [--need-res] [--exclude REGEX] [--src-only FILE] [--exact K]: rank two-region splices
front-of-A (orig tokens [0,k)) + back-of-B ([k,N)) over the index by estimated M = prefM_A(k) + sufM_B(k), both builds
aligned at orig token k (a matching-block boundary in both). Distinct (A,B) pairs keep their best k. --exact prices the
top K pairs with exact difflib M on the spliced token sequence and reports splice bytes."""
import sys,os,json,re,difflib
import numpy as np
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled
from regs import R,reg
LANES=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes')
O=oracle.orig_window(); OT,OO=xled.toks(O); N=len(OT)
def short(p): return os.path.relpath(str(p),LANES).replace('/rx/','/').replace('/fn.bin','')
def load_toks(p):
    raw=open(p,'rb').read() if p.endswith('.bin') else oracle.elf_fn(p,oracle.KEEP)
    return xled.toks(raw)
def exactM(c):
    return sum(b.size for b in difflib.SequenceMatcher(None,OT,c,autojunk=False).get_matching_blocks())
def splice(pa,pb,k,MPa,MPb):
    ta,_=load_toks(pa); tb,_=load_toks(pb)
    c=ta[:MPa[k]]+tb[MPb[k]:]
    return c,sum(len(t) for t in c)
if __name__=='__main__':
    a=sys.argv[1:]; top=40; ex=None; needres=False; exact=0; src=None; kmin=0; kmax=N
    if '--top' in a: i=a.index('--top'); top=int(a[i+1]); del a[i:i+2]
    if '--exclude' in a: i=a.index('--exclude'); ex=re.compile(a[i+1]); del a[i:i+2]
    if '--exact' in a: i=a.index('--exact'); exact=int(a[i+1]); del a[i:i+2]
    if '--src-only' in a: i=a.index('--src-only'); src=set(l.strip() for l in open(a[i+1])); del a[i:i+2]
    if '--need-res' in a: needres=True; a.remove('--need-res')
    Z=np.load(a[0]); names=np.array([str(x) for x in Z['names']]); nb=Z['nbytes']; MP=Z['MP']
    keep=np.ones(len(names),bool)
    for j,p in enumerate(names):
        if needres and not os.path.exists(os.path.join(os.path.dirname(p),'res.json')): keep[j]=False
        if ex and ex.search(short(p)): keep[j]=False
        if src is not None and short(p) not in src: keep[j]=False
    names=names[keep]; nb=nb[keep]; MP=MP[keep]
    hit=MP>=0; Mt=hit.sum(1)
    cs=np.concatenate([np.zeros((len(names),1),dtype=np.int32),np.cumsum(hit,1,dtype=np.int32)],1)
    pref=np.where(hit,cs[:,:-1],-10**6); suf=np.where(hit,Mt[:,None]-cs[:,:-1],-10**6)
    K=6
    fi=np.argsort(-pref,0)[:K]; bi=np.argsort(-suf,0)[:K]
    best={}
    for k in range(N):
        for x in fi[:,k]:
            for y in bi[:,k]:
                if x==y: continue
                e=int(pref[x,k]+suf[y,k])
                if e<0: continue
                if (x,y) not in best or e>best[(x,y)][0]: best[(x,y)]=(e,k)
    rk=sorted(best.items(),key=lambda t:-t[1][0])[:top]
    print(f'builds {len(names)}; main M 2249. top {top} distinct (front,back) pairs by estimated splice M:')
    print(f"{'estM':>5s} {'dM':>4s} {'k':>5s} {'orig':>6s} {'region':12s} {'MA':>5s} {'MB':>5s} front | back")
    rows=[]
    for n,((x,y),(e,k)) in enumerate(rk):
        row=dict(estM=e,k=k,orig=int(OO[k]),region=reg(OO[k]),front=short(names[x]),back=short(names[y]),MA=int(Mt[x]),MB=int(Mt[y]),BA=int(nb[x]),BB=int(nb[y]))
        if n<exact:
            c,b=splice(names[x],names[y],k,MP[x],MP[y]); row['exactM']=exactM(c); row['bytes']=b
        rows.append(row)
        print(f"{e:5d} {e-2249:+4d} {k:5d} {OO[k]:#6x} {reg(OO[k]):12s} {Mt[x]:5d} {Mt[y]:5d} {short(names[x])} | {short(names[y])}"+(f"  exact {row['exactM']} @{row['bytes']}B" if 'exactM' in row else ''))
    json.dump(rows,open(a[0]+'.pairs.json','w'),indent=0)
