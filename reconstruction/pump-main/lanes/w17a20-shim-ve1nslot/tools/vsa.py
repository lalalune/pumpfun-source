#!/usr/bin/env python3
"""vsa.py <ssc-dir> <seed> <secs> [out.json]: annealing over colour processing orders maximising the votes proxy
(aligned spill accesses on their original colour, alignment with spill offsets blanked), legal first-fit colourings only;
then the true M of the best order. Experiment only."""
import sys,os,json,random,math,time
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import sscsim, votes
d,seed,secs=sys.argv[1],int(sys.argv[2]),float(sys.argv[3]); out=sys.argv[4] if len(sys.argv)>4 else None
S,V,n=votes.run(d); random.seed(seed)
def proxy(k): return sum(V[s][k[s]] for s in V)
k0=S.colour(S.order)
want={s:(V[s].most_common(1)[0][0] if V.get(s) else k0[s]) for s in S.order}
starts={'base':list(S.order),'votes':sorted(S.order,key=lambda s:(want[s],-S.W[s]))}
res={}
for nm,cur in starts.items():
    K=S.colour(cur); m=proxy(K); best=(m,list(cur)); t0=time.time(); it=0; T0=3.0
    while time.time()-t0<secs/2:
        it+=1; temp=T0*(1-(time.time()-t0)/(secs/2))+0.05
        o=list(cur); i=random.randrange(len(o)); s=o.pop(i)
        j=min(len(o),max(0,i+int(random.gauss(0,15)))) if random.random()<0.6 else random.randrange(len(o)+1)
        o.insert(j,s); mm=proxy(S.colour(o))
        if mm>=m or random.random()<math.exp((mm-m)/temp):
            cur,m=o,mm
            if m>best[0]: best=(m,list(cur))
    Mb=S.M(S.relabel(S.colour(best[1])))[0]
    res[nm]={'proxy':best[0],'M':Mb,'iters':it,'order':best[1]}
base_proxy=proxy(k0); base_M=S.M(S.relabel(k0))[0]
tot=sum(sum(v.values()) for v in V.values())
print(json.dumps({'d':d,'base_proxy':base_proxy,'tot':tot,'base_M':base_M,**{k:{x:v[x] for x in ('proxy','M','iters')} for k,v in res.items()}}))
if out: json.dump(res,open(out,'w'))
