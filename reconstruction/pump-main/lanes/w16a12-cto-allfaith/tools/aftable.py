#!/usr/bin/env python3
"""aftable.py [res.jsonl] : HxT cross-product table (experiment only).
For every head form H with a capture on main's tail (name h) and on T (name hT), prints M/Mperm/Mhc/LCS for both cells and the
interaction term  I = d(HxT) - d(H) - d(T)  (d = metric minus main's), which is > 0 when the two sides need each other."""
import sys,json,os
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sha=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
f=sys.argv[1] if len(sys.argv)>1 else f'{O}/res-{sha}.jsonl'
R={}
for l in open(f):
    r=json.loads(l)
    if 'M' in r: R[r['name']]=r
# main (1f4e396, lanchorceil n_m, same oracle): bytes 27400 M 2251 Mperm 2295 Mhc 2302 lcs 2257
R.setdefault('m0',{'name':'m0','genes':'-','bytes':27400,'M':2251,'Mperm':2295,'Mhc':2302,'lcs':2257,'lcs_f':2490})
K=('M','Mperm','Mhc','lcs')
m=R['m0']
def d(r,k): return (r.get(k) or 0)-(m.get(k) or 0)
print(f"{'cell':8s} {'genes':44s} {'bytes':>6s} "+' '.join(f'{k:>6s}' for k in K)+'  '+' '.join(f'd{k:>5s}' for k in K)+'   swap Lrfj')
for n,r in sorted(R.items(),key=lambda x:-(x[1].get('Mhc') or 0)):
    print(f"{n:8s} {r['genes'][:44]:44s} {r['bytes']:6d} "+' '.join(f"{r.get(k) or 0:6d}" for k in K)+'  '+' '.join(f'{d(r,k):+6d}' for k in K)+f"   {r.get('swap')} {r.get('Lrfj')}")
print('\ninteraction I = d(HxT) - d(H) - d(T)  per metric')
T=R.get('T')
if T:
    for n,r in R.items():
        if n.endswith('T') and n!='T' and n[:-1] in R:
            H=R[n[:-1]]
            print(f"{n[:-1]:6s} x T : "+'  '.join(f"{k} dH {d(H,k):+5d} dT {d(T,k):+5d} dHT {d(r,k):+5d} I {d(r,k)-d(H,k)-d(T,k):+5d}" for k in ('M','Mhc')))
