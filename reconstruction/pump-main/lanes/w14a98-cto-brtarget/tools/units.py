#!/usr/bin/env python3
"""units.py <m.s>: price B units alone (from main) and leave-one-out (from B), polarity flips allowed."""
import sys,os,json; T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import sub, relayn
p=sys.argv[1]; specf=sys.argv[2] if len(sys.argv)>2 else os.path.dirname(T)+'/tmp/Bspec963.txt'
U=[['bb10.i','bb3.i30.i'],['bb14.i'],['bb23.i'],['bb27.i','bb3.i37.i'],['exit31.i'],['bb16.i'],['bb22.i'],['bb79.i','bb3.i58.i'],['exit59.i'],['bb44.i','bb95.i'],['bb48.i','bb3.i292'],['bb28.i','bb37.i','bb38.i'],['exit38.i'],['bb17.i','bb3.i23.i'],['exit24.i'],['exit293'],['bb39.i','bb3.i51.i']]
m=relayn.irmap(p); Ua=[[m[x] for x in u] for u in U]
spec=open(specf).read().strip().split(',')
names,Bn,_,_,_=sub.border(p,spec)
def sc(order):
    t,fl=sub.emit(p,order,1); s=sub.score(t,os.path.dirname(T)+'/tmp/u.s'); return s['M'],s['bytes'],s['jM'],fl
M0=sc(names); MB=sc(Bn); print('main',M0,'B',MB)
def move(order,u,after):
    o=[x for x in order if x not in u]; i=o.index(after)+1 if after else o.index(Bn[[k for k,x in enumerate(Bn) if x==u[0]][0]+0]) 
    return o[:i]+u+o[i:]
res=[]
for k,u in enumerate(Ua):
    # alone: put u after its B predecessor
    i=Bn.index(u[0]); pred=Bn[i-1]
    o=[x for x in names if x not in u]; j=o.index(pred)+1; alone=sc(o[:j]+u+o[j:])
    # loo: from B put u after its main predecessor
    i=names.index(u[0]); pred=names[i-1]
    o=[x for x in Bn if x not in u]; j=o.index(pred)+1; loo=sc(o[:j]+u+o[j:])
    r=dict(unit=U[k],alone_dM=alone[0]-M0[0],alone_dB=alone[1]-M0[1],alone_djM=alone[2]-M0[2],loo_dM=loo[0]-MB[0],loo_dB=loo[1]-MB[1],loo_djM=loo[2]-MB[2])
    print(json.dumps(r)); res.append(r)
