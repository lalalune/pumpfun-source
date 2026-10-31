#!/usr/bin/env python3
"""ordclimb.py <m.ll> <ss,ss,...> [workers]: best-improvement swap/move climb over the colour rank order of the given top
spill intervals (experiment only; exact, via the private SSC-hook llc). Prints each round's best order and M."""
import sys,os,json
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import sscw
ll=sys.argv[1]; start=[int(x) for x in sys.argv[2].split(',')]; nw=int(sys.argv[3]) if len(sys.argv)>3 else 3
cache={}
def spec(o): return ','.join(f'{s}:={50-i}' for i,s in enumerate(o))
def ev(o):
    k=tuple(o)
    if k not in cache: cache[k]=sscw.run(ll,spec(o))['M']
    return cache[k]
cur=list(start); best=ev(cur); print('start',best,cur,flush=True)
ex=ThreadPoolExecutor(nw)
for rnd in range(12):
    cands=[]
    n=len(cur)
    for i in range(n):
        for j in range(i+1,n):
            o=cur[:]; o[i],o[j]=o[j],o[i]; cands.append(('swap',i,j,o))
    for i in range(n):
        for j in range(n):
            if j in (i,i+1) or abs(i-j)==1: continue
            o=cur[:]; x=o.pop(i); o.insert(j if j<i else j-1,x); cands.append(('move',i,j,o))
    res=list(ex.map(lambda c:(ev(c[3]),c),cands))
    m,c=max(res,key=lambda r:r[0])
    print(f'round {rnd}: best {m} via {c[0]} {c[1]} {c[2]}  (evals {len(cache)})',flush=True)
    if m<=best: break
    best=m; cur=c[3]; print('  order',cur,flush=True)
print(json.dumps({'best':best,'order':cur}))
