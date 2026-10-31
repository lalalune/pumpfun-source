#!/usr/bin/env python3
"""postr.py <results.jsonl> <out.jsonl>: polarity-aware B (Br) on base and h7 asm of each capture (after post.py made them)."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sc, relayn, fbound
R=sc.score(O+'/rx/m/m.o')
done=set()
if os.path.exists(sys.argv[2]):
    for l in open(sys.argv[2]): done.add(json.loads(l)['name'])
for l in open(sys.argv[1]):
    r=json.loads(l); n=r['name']
    if 'ratio' not in r or n in done: continue
    d=f'{O}/rx/{n}'; out=[]
    for v,p in (('base',d+'/m.s'),('h7',d+'/h7.s')):
        if not os.path.exists(p): continue
        x=relayn.run_rev(p,p[:-2]+'Br.s','B'); s=sc.score(p[:-2]+'Br.s'); ch=s.pop('ch')
        s.update({k:v2 for k,v2 in fbound.bound(p[:-2]+'Br.s').items() if k in ('fR','rfR','rfjR')})
        s.update(name=n,v=v+'+Br',miss=x['miss'],flips=x['flips'])
        s['dch']={f'{k:#06x}':[a[0]-R['ch'][k][0],a[1]-R['ch'][k][1]] for k,a in sorted(ch.items())}
        out.append(s)
    with open(sys.argv[2],'a') as f:
        for x in out: f.write(json.dumps(x)+'\n')
    for x in out: print(n,x['v'],{k:x.get(k) for k in ('ratio','bytes','M','jM','fR','rfR','rfjR','skM','flips','miss')})
