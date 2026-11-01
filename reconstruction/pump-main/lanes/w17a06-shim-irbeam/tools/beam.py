#!/usr/bin/env python3
"""beam.py <single.jsonl> <out_combo.txt> [minM] [maxabs] [tol]: build pair jobs from near cells (distinct outputs)."""
import sys,json,itertools
f,outf=sys.argv[1],sys.argv[2]; minM=int(sys.argv[3]) if len(sys.argv)>3 else 2244; maxabs=int(sys.argv[4]) if len(sys.argv)>4 else 64; tol=int(sys.argv[5]) if len(sys.argv)>5 else 8
MAIN=__import__('os').environ.get('MAINSIG','2b6114441bf8')
R=[json.loads(l) for l in open(f)]
pool={}
for r in R:
    if 'M' not in r or r.get('sig')==MAIN: continue
    if '+' in r['id']: continue
    if 'sig' not in r and r['M']==2251 and r['bytes']==27400: continue
    if r['M']<minM or abs(r['bytes']-27400)>maxabs: continue
    k=r.get('sig') or r['id']
    if k not in pool or r['M']>pool[k]['M']: pool[k]=r
P=sorted(pool.values(),key=lambda r:-(r['M']-abs(r['bytes']-27400)/16))
print(len(P),'pool cells')
for r in P[:40]: print(' ',r['id'],r['M']-2251,r['bytes']-27400)
fnline=lambda i: (i.split(':')[1],int(i.split(':')[2]))
jobs=[]
for a,b in itertools.combinations(P,2):
    if abs(a['bytes']+b['bytes']-2*27400)>tol: continue
    ia,ib=a['id'],b['id']
    if fnline(ia)==fnline(ib): continue
    jobs.append((a['M']+b['M']-2251,ia,ib))
jobs.sort(reverse=True)
open(outf,'w').write(''.join(f'{x} {y}\n' for _,x,y in jobs))
print(len(jobs),'pair jobs')
