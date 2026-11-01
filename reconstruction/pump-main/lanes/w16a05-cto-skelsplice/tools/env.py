#!/usr/bin/env python3
"""env.py <idx.npz> [--top N] [--ref main]: region-local M table and two-region splice envelope over an idx.py index.
For every build: per-region matched orig tokens (scorer mask M) minus main's. Then the prefix/suffix envelope:
best front A up to orig token k + best back B from k (both aligned at k), and per-build best single-region insert into main."""
import sys,os,json
import numpy as np
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled,difflib
from regs import R
O=oracle.orig_window(); OT,OO=xled.toks(O); N=len(OT); OO=np.array(OO)
def main_partners():
    C=xled.load('main'); ct,_=xled.toks(C); m=np.full(N,-1,dtype=np.int16)
    for bl in difflib.SequenceMatcher(None,OT,ct,autojunk=False).get_matching_blocks():
        if bl.size: m[bl.a:bl.a+bl.size]=np.arange(bl.b,bl.b+bl.size)
    return m
if __name__=='__main__':
    a=sys.argv[1:]; top=25
    if '--top' in a: i=a.index('--top'); top=int(a[i+1]); del a[i:i+2]
    Z=np.load(a[0]); names=Z['names']; nb=Z['nbytes']; MP=Z['MP']
    mm=main_partners(); mmain=(mm>=0)
    hit=(MP>=0)                       # builds x N
    Mtot=hit.sum(1); print('builds',len(names),'main M',mmain.sum())
    # region masks
    rid=np.zeros(N,dtype=int)
    for k,(lo,hi,n) in enumerate(R): rid[(OO>=lo)&(OO<hi)]=k
    reg=np.stack([hit[:,rid==k].sum(1) for k in range(len(R))],1)
    regm=np.array([mmain[rid==k].sum() for k in range(len(R))])
    d=reg-regm
    print('\nper-region best dM over main (build with max region-local M):')
    for k,(lo,hi,n) in enumerate(R):
        j=int(np.argmax(d[:,k])); print(f'{n:14s} {lo:04x}-{hi:04x} main {regm[k]:4d} tok {(rid==k).sum():4d}  best {d[j,k]:+4d}  n_better {(d[:,k]>0).sum():5d}  {os.path.relpath(str(names[j]),os.path.expanduser("~/.cache/pumpfun-reconstruction/lanes"))} (M {Mtot[j]}, {nb[j]} B)')
    print('sum of per-region best:',d.max(0).clip(0).sum())
    # prefix/suffix envelope
    cs=np.concatenate([np.zeros((len(names),1),dtype=int),np.cumsum(hit,1)],1)   # cs[:,k]=matches in orig[0:k]
    pref=np.where(hit,cs[:,:-1],-10**6)                 # front up to k (k aligned)
    suf=np.where(hit,Mtot[:,None]-cs[:,:-1],-10**6)     # back from k (k aligned)
    bp=pref.max(0); bpi=pref.argmax(0); bs=suf.max(0); bsi=suf.argmax(0)
    E=bp+bs; k=int(np.argmax(E))
    print(f'\nenvelope max {E[k]} at orig tok {k} (orig off {OO[k]:#x}): front {names[bpi[k]]} + back {names[bsi[k]]}')
    np.save(a[0]+'.env.npy',np.stack([bp,bpi,bs,bsi]))
