#!/usr/bin/env python3
"""ux.py <name> <orderfile> fixed|ir [singles|greedy|sets:a.b|...]: unit analysis of an explicit asm-name B order.
Units = maximal runs of the order that are contiguous in the base layout. fixed: fixed-RA relayout oracle. ir: IR moves + real llc."""
import sys,os,json; T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sub, relayn, irord, sc, eseq, irB
R=relayn.R
def load(n,of,src='m.s'):
    d=f'{O}/rx/{n}'; p=d+'/'+src; pre,blocks,post=R.parse(p); names=[x[0] for x in R.explicit(blocks)]
    order=open(of).read().strip().split(','); 
    # units: maximal runs in order that are consecutive in names
    U=[]; 
    for x in order:
        if U and names.index(x)==names.index(U[-1][-1])+1 and order.index(x)==order.index(U[-1][-1])+1: U[-1].append(x)
        else: U.append([x])
    lo=min(names.index(x) for x in order); hi=max(names.index(x) for x in order)
    return d,p,names,order,U,lo,hi
def apply(names,order,U,S):
    o=list(names)
    for k,u in enumerate(U):
        if k not in S: continue
        i=order.index(u[0]); 
        if i==0: continue
        pred=order[i-1]; o=[x for x in o if x not in u]; j=o.index(pred)+1; o=o[:j]+u+o[j:]
    return o
def fixed(p,o,rev=1):
    t,fl=sub.emit(p,o,rev); q=os.path.dirname(p)+'/ux.s'; s=sub.score(t,q)
    return {'M':s['M'],'bytes':s['bytes'],'jM':s['jM'],'fM':s['fM'],'eseq':' '.join(map(str,eseq.seq(sc.fn(q))[:10]))}
def irmv(d,n,names,order,U,S,tag):
    m=irB.irnames(d+'/mi.s'); mv=[]
    for k,u in enumerate(U):
        if k not in S: continue
        i=order.index(u[0])
        if i==0: continue
        j=i-1; pred=order[j]
        while pred not in m: j-=1; pred=order[j]
        p=irord.short(m[pred])
        for x in u:
            if x in m: xi=irord.short(m[x]); mv.append(f'{xi}@{p}'); p=xi
    if not mv: return {'M':None}
    outp=f'{O}/t/{n}_{tag}'; r=irord.run(d+'/mi.ll',outp,'mv:'+';'.join(mv)); r.pop('ch',None)
    if 'err' in r: return r
    return {'M':r['M'],'bytes':r['bytes'],'jM':r['jM'],'fM':r['fM'],'eseq':' '.join(map(str,eseq.seq(sc.fn(outp+'.s'))[:10]))}
if __name__=='__main__':
    n,of,kind=sys.argv[1],sys.argv[2],sys.argv[3]; mode=sys.argv[4] if len(sys.argv)>4 else 'singles'
    if kind=='ir': irB.prep(n)
    d,p,names,order,U,lo,hi=load(n,of,'mi.s' if kind=='ir' else 'm.s'); ALL=set(range(len(U)))
    f=(lambda S,tag: fixed(p,apply(names,order,U,S))) if kind=='fixed' else (lambda S,tag: irmv(d,n,names,order,U,S,tag))
    base=f(set(),'b0') if kind=='fixed' else {'M':None}; full=f(ALL,'all'); print('base',base,'\nall',full,flush=True)
    for k,u in enumerate(U): print(' u%d=%s'%(k,','.join(u)),end='')
    print()
    if mode=='singles':
        for k in range(len(U)): print(k,U[k],json.dumps(f({k},f'x{k}')),flush=True)
    elif mode=='loo':
        for k in range(len(U)): print(k,U[k],'LOO',json.dumps(f(ALL-{k},f'l{k}')),flush=True)
    elif mode.startswith('sets:'):
        for s in mode[5:].split('|'):
            S={int(x) for x in s.split('.') if x}; print(s,json.dumps(f(S,'s'+s.replace('.','_'))),flush=True)
    elif mode=='greedy':
        S=set(); cur=f(set(),'g0') if kind=='ir' else base
        if cur['M'] is None: cur={'M':int(os.environ.get('BASEM','0'))}
        while True:
            best=None
            for k in ALL-S:
                r=f(S|{k},'g'); 
                if r.get('M') is not None and (best is None or r['M']>best[1]['M']): best=(k,r)
            if best is None or best[1]['M']<=cur['M']: break
            S.add(best[0]); cur=best[1]; print('add',best[0],U[best[0]],json.dumps(cur),flush=True)
        print('greedy',sorted(S),json.dumps(cur))
