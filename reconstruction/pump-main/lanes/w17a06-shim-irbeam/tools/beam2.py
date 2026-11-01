#!/usr/bin/env python3
"""beam2.py <single.jsonl> <combo_results.jsonl> <out_jobs.txt> [width] [tol] [minM]: extend top combos by one pool cell."""
import sys,json
sf,cf,outf=sys.argv[1],sys.argv[2],sys.argv[3]; W=int(sys.argv[4]) if len(sys.argv)>4 else 20; tol=int(sys.argv[5]) if len(sys.argv)>5 else 8
minM=int(sys.argv[6]) if len(sys.argv)>6 else 2246
MAIN=__import__('os').environ.get('MAINSIG','2b6114441bf8')
S=[json.loads(l) for l in open(sf)]
pool={}
for r in S:
    if 'M' not in r or r.get('sig')==MAIN or '+' in r['id']: continue
    if 'sig' not in r and r['M']==2251 and r['bytes']==27400: continue
    if r['M']<minM or abs(r['bytes']-27400)>64: continue
    k=r.get('sig') or r['id']
    if k not in pool or r['M']>pool[k]['M']: pool[k]=r
P=list(pool.values())
C=[json.loads(l) for l in open(cf)]
C=[c for c in C if 'M' in c and abs(c['bytes']-27400)<=64]
# rank combos: at-size first by M, then near-size by M - |db|/16
C.sort(key=lambda c:-(c['M']-abs(c['bytes']-27400)/16))
seen=set(); beams=[]
for c in C:
    if c.get('sig') in seen: continue
    seen.add(c.get('sig')); beams.append(c)
    if len(beams)>=W: break
done=set(c['id'] for c in C)
fnline=lambda i: (i.split(':')[1],int(i.split(':')[2]))
jobs=[]
for c in beams:
    ids=c['id'].split('+'); lines={fnline(i) for i in ids}
    for p in P:
        if p['id'] in ids or fnline(p['id']) in lines: continue
        db=c['bytes']+p['bytes']-2*27400
        if abs(db)>tol: continue
        nid='+'.join(sorted(ids+[p['id']]))
        if nid in done: continue
        done.add(nid); jobs.append((c['M']+p['M']-2251,nid))
jobs.sort(reverse=True)
open(outf,'w').write(''.join(j.replace('+',' ')+'\n' for _,j in jobs))
print(len(P),'pool',len(beams),'beams',len(jobs),'jobs')
for c in beams[:10]: print(' beam',c['id'],c['M']-2251,c['bytes']-27400)
