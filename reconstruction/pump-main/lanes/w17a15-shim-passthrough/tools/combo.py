#!/usr/bin/env python3
"""combo.py <edits.jsonl> <singles.jsonl> <base_sig> <M0> <out.txt> [topN] [maxk]: enumerate size-neutral subsets
(sum of single dB = 0) with predicted dM >= 1, no line conflicts, ranked by predicted dM; write the top N as combo lines."""
import sys,json,itertools
ef,sf,bsig,M0,outf=sys.argv[1:6]; M0=int(M0); import os; MIN=int(os.environ.get("CMIN","1")); TOP=int(sys.argv[6]) if len(sys.argv)>6 else 300; K=int(sys.argv[7]) if len(sys.argv)>7 else 4
E={json.loads(l)['id']:json.loads(l) for l in open(ef)}
R={}
for l in open(sf):
    r=json.loads(l)
    if 'M' in r and r['sig']!=bsig: R[r['id']]=r
C=[i for i,r in R.items() if r['M']-M0>=-2 and abs(r['bytes']-27400)<=40]
C.sort(key=lambda i:-(R[i]['M']))
C=C[:60]
def lines(i): return set(int(k) for k in E[i]['rep'])
out=[]
for k in range(1,K+1):
    for sub in itertools.combinations(C,k):
        if sum(R[i]['bytes']-27400 for i in sub)!=0: continue
        dm=sum(R[i]['M']-M0 for i in sub)
        if dm<MIN: continue
        L=set(); bad=False
        for i in sub:
            li=lines(i)
            if L&li: bad=True; break
            L|=li
        if bad: continue
        out.append((dm,k,sub))
out.sort(key=lambda x:(-x[0],x[1]))
open(outf,'w').write(''.join(' '.join(s)+'\n' for _,_,s in out[:TOP]))
print(len(C),len(out),out[:5])
