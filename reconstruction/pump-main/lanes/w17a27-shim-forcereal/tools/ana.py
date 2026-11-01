#!/usr/bin/env python3
"""ana.py <out.jsonl> [main_M] : summarise a fscr screen: identical count, top by M (at 27400 and any size), force hits."""
import sys,json,collections
R=[json.loads(l) for l in open(sys.argv[1]) if l.strip()]
M0=int(sys.argv[2]) if len(sys.argv)>2 else 2295
err=[r for r in R if 'err' in r]; R=[r for r in R if 'M' in r]
c=collections.Counter(r['sig'] for r in R)
print('n',len(R),'err',len(err),'identical',c.get('61dcfe87f489',0))
fk=[k for k in (R[0] if R else {}) if k.startswith('f_') and not k.endswith('_eq')]
def fs(r): return ' '.join(f"{k[2:]}:{r[k][0]}/{r[k][1]}-{r[k][2]}/{r[k][3]}" for k in fk)
print('-- top @27400')
for r in sorted([r for r in R if r['bytes']==27400],key=lambda r:-r['M'])[:12]: print(r['id'],r['M'],r['bytes'],fs(r))
print('-- top any size')
for r in sorted(R,key=lambda r:-r['M'])[:12]: print(r['id'],r['M'],r['bytes'],fs(r))
print('-- force hits (P>=half)')
for k in fk:
    H=[r for r in R if r[k][0]*2>=r[k][1] and r[k][1]>0]
    H.sort(key=lambda r:(-r[k][0],-r['M']))
    print(k,len(H))
    for r in H[:15]: print('  ',r['id'],r['M'],r['bytes'],fs(r))
