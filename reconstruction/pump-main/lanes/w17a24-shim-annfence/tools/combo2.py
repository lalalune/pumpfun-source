#!/usr/bin/env python3
"""combo2.py <edits.jsonl> <singles.jsonl> <base_sig> <M0> <out.txt> [topN] [maxk] [minD] [poolN]: size-neutral subsets
(sum of single dB = 0) of sig-deduplicated cells, predicted dM >= 1 (additive), no line conflicts."""
import sys,json,itertools
ef,sf,bsig,M0,outf=sys.argv[1:6]; M0=int(M0)
TOP=int(sys.argv[6]) if len(sys.argv)>6 else 300; K=int(sys.argv[7]) if len(sys.argv)>7 else 4
MIND=int(sys.argv[8]) if len(sys.argv)>8 else -2; POOL=int(sys.argv[9]) if len(sys.argv)>9 else 70
E={}
for l in open(ef):
    e=json.loads(l); E[e['id']]=e
R={}
for l in open(sf):
    r=json.loads(l)
    if 'M' in r and r['sig']!=bsig and '+' not in r['id']: R[r['id']]=r
bysig={}
for i,r in sorted(R.items(),key=lambda x:(-x[1]['M'],x[0])):
    bysig.setdefault(r['sig'],i)
C=[i for i in bysig.values() if R[i]['M']-M0>=MIND and abs(R[i]['bytes']-27400)<=40]
C.sort(key=lambda i:-(R[i]['M']))
C=C[:POOL]
def lines(i): return set(int(k) for k in E[i]['rep'])
out=[]
for k in range(1,K+1):
    for sub in itertools.combinations(C,k):
        if sum(R[i]['bytes']-27400 for i in sub)!=0: continue
        dm=sum(R[i]['M']-M0 for i in sub)
        if dm<1: continue
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
