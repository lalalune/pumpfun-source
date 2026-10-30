#!/usr/bin/env python3
"""frgreedy.py <m.ll> <sweep.jsonl> OUT.jsonl [rounds] [topk]: greedy accumulation of frame items (plain ratio)."""
import sys,json,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import frsweep,bwx
from concurrent.futures import ThreadPoolExecutor
mod=open(sys.argv[1]).read(); ot=bwx.orig_toks()
r=[json.loads(l) for l in open(sys.argv[2])]; r=[x for x in r if 'ratio' in x]; r.sort(key=lambda x:-x['ratio'])
rounds=int(sys.argv[4]) if len(sys.argv)>4 else 6; K=int(sys.argv[5]) if len(sys.argv)>5 else 30
cands=[x['item'] for x in r[:K]]; f=open(sys.argv[3],'a')
cur=[]; best=frsweep.run(mod,'',ot)['ratio']
for rd in range(rounds):
    pool=[c for c in cands if c not in cur and not any(c.split(':')[1]==u.split(':')[1] for u in cur)]
    with ThreadPoolExecutor(2) as ex: res=list(ex.map(lambda c: frsweep.run(mod,','.join(cur+[c]),ot),pool))
    res=[x for x in res if 'ratio' in x]; res.sort(key=lambda x:-x['ratio'])
    if not res or res[0]['ratio']<=best: break
    best=res[0]['ratio']; cur=res[0]['spec'].split(','); f.write(json.dumps({'round':rd,**res[0]})+'\n'); f.flush()
