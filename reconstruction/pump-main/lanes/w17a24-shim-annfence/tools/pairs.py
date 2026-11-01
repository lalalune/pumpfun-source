#!/usr/bin/env python3
"""pairs.py <singles[,more]> <base_sig> <M0> <out.txt> [minA] [minB] [maxB]: off-size improver x exact repay pairs.
A = cells with dM >= minA and dB != 0; B = cells with dM >= minB whose dB repays A exactly (pairs) or two B cells
repay A (triples, only for |dB(A)| <= maxB). Sig-deduplicated; no line conflicts checked here (the screen reports them)."""
import sys,json,itertools
sfs,bsig,M0,outf=sys.argv[1:5]; M0=int(M0)
minA=int(sys.argv[5]) if len(sys.argv)>5 else 0; minB=int(sys.argv[6]) if len(sys.argv)>6 else -4
maxB=int(sys.argv[7]) if len(sys.argv)>7 else 24
R={}
for sf in sfs.split(','):
    for l in open(sf):
        r=json.loads(l)
        if 'M' in r and '+' not in r['id'] and r['sig']!=bsig: R[r['id']]=r
bysig={}
for i,r in sorted(R.items(),key=lambda x:(-x[1]['M'],x[0])): bysig.setdefault(r['sig'],i)
C=[bysig[s] for s in bysig]
A=[i for i in C if R[i]['M']-M0>=minA and R[i]['bytes']!=27400 and abs(R[i]['bytes']-27400)<=maxB]
out=[]
for a in A:
    need=27400-R[a]['bytes']
    B=[b for b in C if b!=a and R[b]['M']-M0>=minB and R[b]['bytes']-27400==need]
    out+=[(R[a]['M']+R[b]['M']-2*M0,a,b) for b in B]
out.sort(key=lambda x:-x[0])
open(outf,'w').write(''.join(f'{a} {b}\n' for _,a,b in out))
print(len(A),'A cells',len(out),'pairs')
