#!/usr/bin/env python3
"""uo.py <name> [mode]: per-unit prices of B at fixed RA on rx/<name>/m.s (units = w14a98 units_def renamed for current main;
names resolved by content from rx/main/m.s). mode: units (alone/LOO) | greedy | sets"""
import sys,os,json; T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sub, relayn
U=[['bb10.i','bb3.i30.i'],['bb14.i'],['bb23.i'],['bb27.i','bb3.i37.i'],['exit31.i'],['bb16.i'],['bb22.i'],['bb79.i','bb3.i58.i'],['exit59.i'],['bb44.i','bb95.i'],['bb48.i','bb3.i291'],['bb28.i','bb37.i','bb38.i'],['exit38.i'],['bb17.i','bb3.i23.i'],['exit24.i'],['exit292'],['bb39.i','bb3.i51.i']]
def setup(n,specf):
    p=f'{O}/rx/{n}/m.s'; spec=open(f'{O}/tmp/{specf}').read().strip().split(',')
    rs=sub.resolve_content(f'{O}/rx/main/m.s',p,spec); mp={a:b for a,b in zip(spec,rs) if b}
    names,Bn,miss=sub.border2(f'{O}/rx/main/m.s',p,spec)
    units=[[mp[x] for x in u if x in mp] for u in U]
    return p,names,Bn,units
def order_for(names,Bn,units,S):
    o=list(names)
    for k,ua in enumerate(units):
        if k not in S or not ua: continue
        i=Bn.index(ua[0]); pred=Bn[i-1]
        o=[x for x in o if x not in ua]; j=o.index(pred)+1; o=o[:j]+ua+o[j:]
    return o
def loo(names,Bn,units,k):
    ua=units[k]
    if not ua: return list(Bn)
    i=names.index(ua[0]); pred=names[i-1]; o=[x for x in Bn if x not in ua]; j=o.index(pred)+1
    return o[:j]+ua+o[j:]
def price(p,o,rev=1):
    t,fl=sub.emit(p,o,rev); s=sub.score(t,os.path.dirname(p)+'/us.s'); return s['M'],s['bytes'],s['jM'],s['fM'],fl
if __name__=='__main__':
    n=sys.argv[1]; mode=sys.argv[2] if len(sys.argv)>2 else 'units'; specf=os.environ.get('SPEC','Bspec_O.txt')
    p,names,Bn,units=setup(n,specf); N=len(U); ALL=set(range(N))
    base=price(p,names); full=price(p,order_for(names,Bn,units,ALL)); print('base',base,'B(all units)',full)
    if mode=='units':
        for k in range(N):
            a=price(p,order_for(names,Bn,units,{k})); l=price(p,loo(names,Bn,units,k))
            print(f'{k:2d} {",".join(U[k]):24s} alone dM {a[0]-base[0]:+4d} ({a[1]}) LOO dM {l[0]-full[0]:+4d} ({l[1]})',flush=True)
    elif mode=='greedy':
        S=set(); cur=base
        while True:
            best=None
            for k in ALL-S:
                r=price(p,order_for(names,Bn,units,S|{k}))
                if best is None or r[0]>best[1][0]: best=(k,r)
            if best is None or best[1][0]<=cur[0]: break
            S.add(best[0]); cur=best[1]; print('add',best[0],U[best[0]],cur,flush=True)
        print('greedy',sorted(S),cur)
