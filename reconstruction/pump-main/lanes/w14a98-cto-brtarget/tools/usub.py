#!/usr/bin/env python3
"""usub.py <m.s> <subset-of-unit-indices|name> ...: apply B unit moves for a subset (each unit placed after its B predecessor, in B order)."""
import sys,os,json; T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import sub, relayn, units_def as U
def order_for(p,S):
    m=relayn.irmap(p); spec=open(os.path.dirname(T)+'/tmp/Bspec963.txt').read().strip().split(',')
    names,Bn,_,_,_=sub.border(p,spec); o=list(names)
    for k,u in enumerate(U.U):
        if k not in S: continue
        ua=[m[x] for x in u]; i=Bn.index(ua[0]); pred=Bn[i-1]
        o=[x for x in o if x not in ua]; j=o.index(pred)+1; o=o[:j]+ua+o[j:]
    return o
def price(p,S,rev=1):
    o=order_for(p,S); t,fl=sub.emit(p,o,rev); s=sub.score(t,os.path.dirname(T)+'/tmp/us.s'); return s['M'],s['bytes'],s['jM'],fl
if __name__=='__main__':
    p=sys.argv[1]
    for a in sys.argv[2:]:
        S=U.SETS[a] if a in U.SETS else [int(x) for x in a.split('.')]
        print(a,price(p,set(S)))
