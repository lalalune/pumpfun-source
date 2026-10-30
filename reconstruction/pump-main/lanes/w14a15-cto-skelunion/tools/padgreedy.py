#!/usr/bin/env python3
"""padgreedy.py <m.ll> <rounds> <log.jsonl> [start-spec]: greedy 8-B asm-pad placement (oracle bound). Each round scans every
execute block with one more pad on the current spec and keeps the best."""
import sys,os,json,concurrent.futures as cf
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import pad
t0=open(sys.argv[1]).read(); R=int(sys.argv[2]); log=sys.argv[3]; spec=dict()
if len(sys.argv)>4 and sys.argv[4]:
    for x in sys.argv[4].split(','): l,k=x.rsplit(':',1); spec[l]=int(k)
def build(sp):
    t=t0
    for l,k in sp.items(): t=pad.ins(t,l,k)
    return t
labs=pad.labels(t0)
for rnd in range(R):
    def go(l):
        sp=dict(spec); sp[l]=sp.get(l,0)+1; return l,pad.score(build(sp),l)
    with cf.ThreadPoolExecutor(2) as ex: res=list(ex.map(go,labs))
    res=[(l,r) for l,r in res if 'ratio' in r]; res.sort(key=lambda x:-x[1]['ratio'])
    l,r=res[0]; spec[l]=spec.get(l,0)+1
    open(log,'a').write(json.dumps({'round':rnd,'pick':l,**r,'spec':','.join(f'{a}:{b}' for a,b in spec.items()),'top5':[(a,b['ratio'],b['bytes']) for a,b in res[:5]]})+'\n')
