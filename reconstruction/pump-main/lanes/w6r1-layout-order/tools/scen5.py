import sys,json,re,itertools
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2]); g=datamap(M,sys.argv[1])
fix=lambda a: M.wins[M.inv[a]]['bytes'] if a in M.inv and M.inv[a] in M.UN else M.units[a][0]
base=M.eval(M.cst)
def mv(order,moves):
    for st in moves:
        a=M.pair[st]; o=[x for x in order if x!=a]
        # place after unit whose orig start is the greatest < st among L
        prev=max((x for x in o if x in M.inv and M.inv[x]<st), key=lambda x:M.inv[x])
        i=o.index(prev)+1; order=o[:i]+[a]+o[i:]
    return order
H=[0x13b9b8,0x13f630,0x147ba0,0x1489f8,0x14a8a8,0x969f0]
for k in range(1,len(H)+1):
  for sub in itertools.combinations(H,k):
    o=mv(list(M.cst),sub); r=M.eval(o)
    o2=[a for a in o if a in M.inv]; r2=M.eval(o2,fix)
    if len(r)!=len(base) or k==len(H): print([hex(x) for x in sub],'now',len(r),'+',len(r-base),'-',sorted(hex(x) for x in base-r)[:8],'| P8',len(r2))
