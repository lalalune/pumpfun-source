#!/usr/bin/env python3
"""sa2.py <ssc-dir> <seed> <secs> <out.json> [init=votes|base]: annealing over colour processing orders (sscsim), optionally
started from a votes-guided order (intervals sorted by their majority original colour, then weight). Experiment only."""
import sys,os,json,random,math,time
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import sscsim, votes
d,seed,secs,out=sys.argv[1],int(sys.argv[2]),float(sys.argv[3]),sys.argv[4]; init=sys.argv[5] if len(sys.argv)>5 else 'votes'
S,V,n=votes.run(d); random.seed(seed)
k0=S.colour(S.order)
if init=='votes':
    want={s:(V[s].most_common(1)[0][0] if V.get(s) else k0[s]) for s in S.order}
    cur=sorted(S.order,key=lambda s:(want[s],-S.W[s]))
else: cur=list(S.order)
K=S.colour(cur); m=S.M(S.relabel(K))[0]; best=(m,list(cur)); cache={}; start=m
t0=time.time(); it=0; T0=2.0
while time.time()-t0<secs:
    it+=1; temp=T0*(1-(time.time()-t0)/secs)+0.05
    o=list(cur); i=random.randrange(len(o)); s=o.pop(i)
    j=min(len(o),max(0,i+int(random.gauss(0,12)))) if random.random()<0.7 else random.randrange(len(o)+1)
    o.insert(j,s); k=S.colour(o); key=tuple(k[x] for x in S.fis)
    if key in cache: mm=cache[key]
    else: mm=S.M(S.relabel(k))[0]; cache[key]=mm
    if mm>=m or random.random()<math.exp((mm-m)/temp):
        cur,m=o,mm
        if m>best[0]: best=(m,list(cur))
json.dump({'M':best[0],'start':start,'order':best[1],'iters':it,'uniq':len(cache)},open(out,'w'))
print(init,'start',start,'best',best[0],it,len(cache))
