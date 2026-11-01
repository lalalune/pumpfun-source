#!/usr/bin/env python3
"""idx.py <list.txt> <out.npz> [--jobs N] [--lanes DIR] [--skel] [--minratio R]: index archived admin_cto builds
(fn.bin, m.o or unstripped.so; any path). Dedupes by byte hash; for each unique build stores the per-orig-token partner
index under the scorer mask (M; -1 = unmatched) and, with --skel, under the skeleton mask (xled.fmask)."""
import sys,os,difflib,hashlib,json
import numpy as np
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled
from multiprocessing import Pool
O=oracle.orig_window(); OT,OO=xled.toks(O); OF=xled.fmask(OT); N=len(OT)
SKEL=False
def load(p):
    if p.endswith('.bin'): return open(p,'rb').read()
    return oracle.elf_fn(p,oracle.KEEP)
def partners(a,b):
    m=np.full(N,-1,dtype=np.int16)
    for bl in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        if bl.size: m[bl.a:bl.a+bl.size]=np.arange(bl.b,bl.b+bl.size,dtype=np.int16)
    return m
def work(args):
    p,skel=args
    try: raw=load(p)
    except Exception as e: return p,None,None,None,str(e)
    ct,co=xled.toks(raw)
    mp=partners(OT,ct)
    sp=partners(OF,xled.fmask(ct)) if skel else np.full(N,-1,dtype=np.int16)
    return p,len(raw),mp,sp,None
def save(res,out):
    names=np.array([r[0] for r in res]); nbytes=np.array([r[1] for r in res])
    MP=np.stack([r[2] for r in res]); SP=np.stack([r[3] for r in res])
    np.savez_compressed(out,names=names,nbytes=nbytes,MP=MP,SP=SP)
if __name__=='__main__':
    a=sys.argv[1:]; jobs=6; base=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes'); skel=False; minr=None
    if '--jobs' in a: i=a.index('--jobs'); jobs=int(a[i+1]); del a[i:i+2]
    if '--lanes' in a: i=a.index('--lanes'); base=a[i+1]; del a[i:i+2]
    if '--minratio' in a: i=a.index('--minratio'); minr=float(a[i+1]); del a[i:i+2]
    if '--skel' in a: skel=True; a.remove('--skel')
    paths=[l.strip() for l in open(a[0]) if l.strip()]
    paths=[p if p.startswith('/') else os.path.join(base,p) for p in paths]
    seen={}; uniq=[]; dup={}
    for p in paths:
        if minr is not None:
            try:
                r=json.load(open(os.path.join(os.path.dirname(p),'res.json'))).get('ratio')
                if r is not None and r<minr: continue
            except Exception: pass
        try: raw=load(p)
        except Exception: continue
        if not (26000<=len(raw)<=29000): continue
        h=hashlib.sha1(raw).hexdigest()[:16]
        if h in seen: dup.setdefault(seen[h],[]).append(p); continue
        seen[h]=p; uniq.append(p)
    print('paths',len(paths),'unique',len(uniq),flush=True)
    json.dump(dup,open(a[1]+'.dups.json','w'))
    res=[]
    with Pool(jobs) as pool:
        for k,(p,nb,mp,sp,err) in enumerate(pool.imap_unordered(work,[(p,skel) for p in uniq],chunksize=8)):
            if err: continue
            res.append((p,nb,mp,sp))
            if k%500==499: print(k+1,flush=True); save(res,a[1])
    save(res,a[1]); print('saved',len(res),flush=True)
