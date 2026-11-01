#!/usr/bin/env python3
"""wg.py <name> [rounds]: greedy branch-weight search over validate's conditional branches (post-opt IR !prof, real llc), parallel.
Weights per branch: none,1:1,20:12,12:20,2:1,1:2,1:20,20:1. Objective M (ties: fewer bytes). Writes t/wg_<name>.log"""
import sys,os,json,re; T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import irord
from concurrent.futures import ThreadPoolExecutor
n=sys.argv[1]; rounds=int(sys.argv[2]) if len(sys.argv)>2 else 3; P=int(os.environ.get('PAR','2'))
ll=f'{O}/rx/{n}/mi.ll'; t=open(ll).read(); pre,bl,post=irord.split(t); nm=[irord.short(b[0]) for b in bl]
i0=nm.index('bb6.i'); i1=nm.index('bb75')
B=[irord.short(bl[i][0]) for i in range(i0,i1) if bl[i][1].rstrip().split('\n')[-1].strip().startswith('br i1')]
W=[None,'1:1','20:12','12:20','2:1','1:2','1:20','20:1']
cur=eval(os.environ.get('WSTART','{}')); log=open(f'{O}/t/wg_{n}.log','a')
def ev(c,tag):
    pr=','.join(f'{k}={v}' for k,v in c.items() if v)
    r=irord.run(ll,f'{O}/t/wg_{n}_{tag}','',pr or None)
    return (r.get('M',0),-(r.get('bytes') or 0)),r
best,br=ev(cur,'s'); print('start',cur,br,file=log,flush=True); print('branches',B,file=log,flush=True)
for rnd in range(rounds):
    cands=[]
    for b in B:
        for w in W:
            if cur.get(b)==w: continue
            c=dict(cur); c[b]=w; cands.append(c)
    with ThreadPoolExecutor(P) as ex:
        res=list(ex.map(lambda kc: ev(kc[1],str(kc[0]%P)), enumerate(cands)))
    k=max(range(len(res)),key=lambda i: res[i][0])
    print('round',rnd,'best',cands[k],res[k][1],file=log,flush=True)
    top=sorted(range(len(res)),key=lambda i: res[i][0],reverse=True)[:8]
    for i in top: print('   ',cands[i],res[i][1].get('M'),res[i][1].get('bytes'),res[i][1].get('jM'),file=log,flush=True)
    if res[k][0]<=best: break
    best=res[k][0]; cur=cands[k]
print('final',cur,best,file=log,flush=True)
