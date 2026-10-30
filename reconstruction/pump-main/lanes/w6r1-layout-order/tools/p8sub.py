import sys,json,re,itertools
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2]); g=datamap(M,sys.argv[1])
def mv(order,moves):
    for st in moves:
        a=M.pair[st]; o=[x for x in order if x!=a]
        prev=max((x for x in o if x in M.inv and M.inv[x]<st), key=lambda x:M.inv[x])
        i=o.index(prev)+1; order=o[:i]+[a]+o[i:]
    return order
fx=set(M.pair[s] for s in M.UN)
sz=lambda a: M.wins[M.inv[a]]['bytes'] if a in fx else M.units[a][0]
H=[0x13b9b8,0x13f630,0x147ba0,0x1489f8,0x14a8a8,0x969f0]
for k in range(0,len(H)+1):
  for sub in itertools.combinations(H,k):
    o=mv(list(M.cst),sub); r=M.eval(o,sz); n=len([s for s in r if g[s]])
    print([hex(x) for x in sub],'P8',n,'now',len(M.eval(o)))
