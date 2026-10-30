import sys,json,re,itertools
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2]); g=datamap(M,sys.argv[1])
er=[a for a in M.cst if a not in M.inv][0]
U=sorted(M.UN)
def mvh(order):
    for st in [0x13b9b8,0x13f630,0x147ba0,0x1489f8,0x14a8a8,0x969f0]:
        a=M.pair[st]; o=[x for x in order if x!=a]
        prev=max((x for x in o if x in M.inv and M.inv[x]<st), key=lambda x:M.inv[x])
        i=o.index(prev)+1; order=o[:i]+[a]+o[i:]
    return order
def ev(order,fixed,drop_er):
    fx=set(M.pair[s] for s in fixed)
    sz=lambda a: M.wins[M.inv[a]]['bytes'] if a in fx else M.units[a][0]
    o=[a for a in order if not (drop_er and a==er)]
    r=M.eval(o,sz)
    tsz=sum(sz(a) for a in o)
    return len([s for s in r if g[s]]), tsz==M.osec['.text']['size']
for name,order in [('as-built',list(M.cst)),('handlers@program',mvh(list(M.cst)))]:
    print('==',name,'none',ev(order,[],False),'drop-extra',ev(order,[],True),'all',ev(order,U,True),'all-keep-extra',ev(order,U,False))
    for s in U: print('  only',hex(s),ev(order,[s],False),'| all-but',ev(order,[x for x in U if x!=s],True))
    # greedy
    fixed=[];rem=list(U);seq=[]
    while rem:
        best=max(rem,key=lambda s: ev(order,fixed+[s],False)[0]); fixed.append(best); rem.remove(best); seq.append((hex(best),ev(order,fixed,False)[0]))
    print('  greedy (extra kept)',seq,'then drop extra',ev(order,fixed,True))
