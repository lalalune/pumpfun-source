#!/usr/bin/env python3
"""npairs.py <singles[,more]> <base_sig> <M0> <out.txt> [minD] [k]: all k-subsets (k=2 default; 3 adds triples) of
sig-distinct cells at exactly 27,400 B with dM >= minD (non-additive combination screen)."""
import sys,json,itertools
sfs,bsig,M0,outf=sys.argv[1:5]; M0=int(M0); minD=int(sys.argv[5]) if len(sys.argv)>5 else -1; K=int(sys.argv[6]) if len(sys.argv)>6 else 2
R={}
for sf in sfs.split(','):
    for l in open(sf):
        r=json.loads(l)
        if 'M' in r and '+' not in r['id'] and r['sig']!=bsig: R[r['id']]=r
bysig={}
for i,r in sorted(R.items(),key=lambda x:(-x[1]['M'],x[0])): bysig.setdefault(r['sig'],i)
C=[i for i in bysig.values() if R[i]['bytes']==27400 and R[i]['M']-M0>=minD]
out=[]
for k in range(2,K+1):
    out+=[' '.join(s) for s in itertools.combinations(sorted(C),k)]
open(outf,'w').write('\n'.join(out)+'\n'); print(len(C),'cells',len(out),'subsets')
