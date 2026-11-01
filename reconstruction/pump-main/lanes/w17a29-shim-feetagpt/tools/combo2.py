#!/usr/bin/env python3
"""combo2.py <edits.jsonl> <singles.jsonl> <base_sig> <M0> <B0> <target_bytes> <out.txt> [topN] [maxk] [minpred]:
subsets whose single dB sum to target-B0, no line conflicts, ranked by predicted dM."""
import sys,json,itertools
ef,sf,bsig,M0,B0,TB,outf=sys.argv[1:8]; M0=int(M0); B0=int(B0); TB=int(TB)
TOP=int(sys.argv[8]) if len(sys.argv)>8 else 300; K=int(sys.argv[9]) if len(sys.argv)>9 else 4; MINP=int(sys.argv[10]) if len(sys.argv)>10 else 1
E={}
for l in open(ef):
    e=json.loads(l); E[e['id']]=e
R={}
for l in open(sf):
    r=json.loads(l)
    if 'M' in r and r['sig']!=bsig: R[r['id']]=r
C=[i for i,r in R.items() if r['M']-M0>=-8 and abs(r['bytes']-B0)<=48]
C.sort(key=lambda i:-(R[i]['M']-M0))
C=C[:70]
need=TB-B0
def lines(i): return set(int(k) for k in E[i]['rep'])
out=[]
for k in range(1,K+1):
    for sub in itertools.combinations(C,k):
        if sum(R[i]['bytes']-B0 for i in sub)!=need: continue
        dm=sum(R[i]['M']-M0 for i in sub)
        if dm<MINP: continue
        L=set(); bad=False
        for i in sub:
            li=lines(i)
            if L&li: bad=True; break
            L|=li
        if bad: continue
        out.append((dm,k,sub))
out.sort(key=lambda x:(-x[0],x[1]))
open(outf,'w').write(''.join(' '.join(s)+'\n' for _,_,s in out[:TOP]))
print(len(C),len(out),[(d,k,' '.join(s)) for d,k,s in out[:8]])
