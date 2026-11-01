#!/usr/bin/env python3
"""fsa.py <ssc-dir> <seed> <secs> [out.json]: fast annealing over colour processing orders with a true-LCS proxy
(rapidfuzz LCSseq on scorer-masked tokens), then difflib M (the scorer's metric) of the best orders. Experiment only."""
import sys,os,json,random,math,time
from rapidfuzz.distance import LCSseq
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import sscsim
d,seed,secs=sys.argv[1],int(sys.argv[2]),float(sys.argv[3]); out=sys.argv[4] if len(sys.argv)>4 else None
S=sscsim.Sim(d); random.seed(seed)
OH=[hash(t) for t in S.O]
def lcs(k):
    return LCSseq.similarity(OH,[hash(t) for t in sscsim.oracle.mask(S.relabel(k))])
cur=list(S.order); m=lcs(S.colour(cur)); base=m; best=(m,list(cur)); top=[]
t0=time.time(); it=0; T0=3.0; cache={}
while time.time()-t0<secs:
    it+=1; temp=T0*(1-(time.time()-t0)/secs)+0.05
    o=list(cur); i=random.randrange(len(o)); s=o.pop(i)
    j=min(len(o),max(0,i+int(random.gauss(0,12)))) if random.random()<0.7 else random.randrange(len(o)+1)
    o.insert(j,s); k=S.colour(o); key=tuple(k[x] for x in S.fis)
    if key in cache: mm=cache[key]
    else: mm=lcs(k); cache[key]=mm
    if mm>=m or random.random()<math.exp((mm-m)/temp):
        cur,m=o,mm
        if m>best[0]: best=(m,list(cur)); top.append((m,list(cur)))
top=sorted(top,key=lambda x:-x[0])[:6]
evals=[(l,S.M(S.relabel(S.colour(o)))[0]) for l,o in top]
bm=max(evals,key=lambda x:x[1]) if evals else (base,None)
basem=S.M(S.relabel(S.colour(S.order)))[0]
res={'d':d,'seed':seed,'iters':it,'uniq':len(cache),'lcs_base':base,'lcs_best':best[0],'M_base':basem,'M_of_top':evals}
print(json.dumps(res))
if out: json.dump({'res':res,'order':best[1]},open(out,'w'))
