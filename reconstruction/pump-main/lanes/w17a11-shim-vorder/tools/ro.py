#!/usr/bin/env python3
"""ro.py <name> <order> [--base m.ll] [--w spec] [--keep]: reorder execute's IR blocks: the listed blocks (space separated, TS.exitNN
shorthand allowed) are placed, in the given order, at the position of the first listed block; others keep relative order."""
import sys,os,re,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import px,oracle,mv
OUT=os.path.dirname(T)
TS='_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h1551814bef63e52cE'
def full(n): return n.replace('TS.',TS+'.')
def reorder(t,order):
    t=mv.denum(t)
    L,st,en,S=mv.blocks(t)
    B=[(s,(S[k+1] if k+1<len(S) else en)) for k,s in enumerate(S)]
    names=[mv.name_of(L[s]) for s,_ in B]
    want=[full(x) for x in order.split()]
    for w in want: assert w in names,w
    idx={n:i for i,n in enumerate(names)}
    first=min(idx[w] for w in want)
    seq=[i for i in range(len(B)) if names[i] not in want]
    # insert wanted blocks at the position of 'first' among the kept ones
    pos=sum(1 for i in seq if i<first)
    seq=seq[:pos]+[idx[w] for w in want]+seq[pos:]
    body=[]
    for i in seq: body+=L[B[i][0]:B[i][1]]
    L2=L[:S[0]]+body+L[en:]
    return '\n'.join(L2)
if __name__=='__main__':
    a=sys.argv[1:]; name=a[0]; order=a[1]; base=OUT+'/fx/m0/m.ll'; w=''
    if '--base' in a: base=a[a.index('--base')+1]
    if '--w' in a: w=a[a.index('--w')+1]
    t=reorder(open(base).read(),order)
    d=OUT+'/px'; os.makedirs(d,exist_ok=True); p=d+'/ro_'+name+'.ll'; open(p,'w').write(t)
    r=px.run(name,w,p)
    if '--keepll' not in a: os.remove(p)
    r['order']=order[:80]; print(json.dumps(r))
