#!/usr/bin/env python3
"""greedy.py <base.ll> <edits.jsonl> <singles.jsonl> <out.jsonl> <start ids,comma> [workers] [rounds]: greedy forward selection at 27,400 B."""
import sys,os,json
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import fx, screen
base,ef,sf,outf,start=sys.argv[1:6]; W=int(sys.argv[6]) if len(sys.argv)>6 else 4; RN=int(sys.argv[7]) if len(sys.argv)>7 else 4
L=open(base).read().split('\n'); E={}
for l in open(ef):
    e=json.loads(l); E[e['id']]=e
S=[json.loads(l) for l in open(sf)]; S=[r for r in S if 'M' in r]
M0=2270
cand=[r['id'] for r in S if r['sig']!='6ebb02255691' and r['M']-M0>=-3 and abs(r['bytes']-27400)<=16]
cur=start.split(',') if start else []
cache={}
if os.path.exists(outf):
    for l in open(outf):
        r=json.loads(l); cache[r['id']]=r
def ev(ids):
    k='+'.join(sorted(ids))
    if k in cache: return cache[k]
    t=screen.apply(L,[E[i] for i in ids])
    if t is None: r={'id':k,'err':'conflict'}
    else:
        nm='g'+str(abs(hash(k))%10**9); r=fx.run(t,nm); r['id']=k; r.pop('name',None)
        import shutil; shutil.rmtree(os.path.join(fx.OUT,'fx',nm),ignore_errors=True)
    cache[k]=r
    with open(outf,'a') as f: f.write(json.dumps(r)+'\n')
    return r
best=ev(cur) if cur else {'M':M0,'bytes':27400}
print('start',cur,best.get('M'),best.get('bytes'),flush=True)
for rnd in range(RN):
    trials=[c for c in cand if c not in cur]
    with ThreadPoolExecutor(W) as ex: res=list(ex.map(lambda c:(c,ev(cur+[c])),trials))
    ok=[(c,r) for c,r in res if 'M' in r and r['bytes']==27400]
    if not ok: break
    c,r=max(ok,key=lambda x:x[1]['M'])
    print('round',rnd,'best add',c,r['M'],flush=True)
    if r['M']<=best['M']: break
    cur.append(c); best=r
print('final',cur,best,flush=True)
