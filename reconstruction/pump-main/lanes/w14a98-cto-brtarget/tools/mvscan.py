#!/usr/bin/env python3
"""mvscan.py <m.s> <block-short-names comma> : move a unit to every legal slot (after a block with no fallthrough), fixed RA."""
import sys,os,json; T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import sub, relayn
R=relayn.R
p=sys.argv[1]; u=sys.argv[2].split(','); lo=int(sys.argv[3]) if len(sys.argv)>3 else 0; hi=int(sys.argv[4]) if len(sys.argv)>4 else 10**9
m=relayn.irmap(p); inv={v:k for k,v in m.items()}; ua=[m[x] for x in u]
pre,blocks,post=R.parse(p); eb=R.explicit(blocks); names=[x[0] for x in eb]; ft={x[0]:x[2] for x in eb}
base=[x for x in names if x not in ua]
t,_=sub.emit(p,names,0); s0=sub.score(t,os.path.dirname(T)+'/tmp/mv.s')
res=[]
for j in range(1,len(base)):
    if not (lo<=j<=hi): continue
    prev=base[j-1]
    legal = ft[prev] is None
    o=base[:j]+ua+base[j:]
    t,_=sub.emit(p,o,0); s=sub.score(t,os.path.dirname(T)+'/tmp/mv.s')
    res.append((s['M']-s0['M'],s['bytes']-s0['bytes'],s['jM']-s0['jM'],j,inv.get(prev,prev),legal))
res.sort(reverse=True)
for r in res[:25]: print(r)
