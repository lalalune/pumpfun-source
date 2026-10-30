import sys,re; sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2]); g=datamap(M,sys.argv[1])
bad=[s for s,v in g.items() if not v]
print('data-offset-equal',sum(g.values()),'of',len(g),'bad',[hex(s) for s in bad])
# pay_out_native swap scenario
fx=set(M.pair[s] for s in M.UN)
sz=lambda a: M.wins[M.inv[a]]['bytes'] if a in fx else M.units[a][0]
def mvh(order,sts):
    for st in sts:
        a=M.pair[st]; o=[x for x in order if x!=a]
        prev=max((x for x in o if x in M.inv and M.inv[x]<st), key=lambda x:M.inv[x])
        i=o.index(prev)+1; order=o[:i]+[a]+o[i:]
    return order
for nm,o in [('as-built',list(M.cst)),('bh moved',mvh(list(M.cst),[0x13b9b8])),('bh+pon',mvh(list(M.cst),[0x13b9b8,0x969f0])),('pon',mvh(list(M.cst),[0x969f0]))]:
    oo=[a for a in o if a in M.inv]; r=M.eval(oo,sz)
    print(nm,'P8',len([s for s in r if g[s]]),'P8-dataok-assumed',len(r))
full=sorted([a for a in M.cst if a in M.inv],key=lambda a:M.inv[a]); r=M.eval(full,sz); print('full order',len([s for s in r if g[s]]),len(r))
