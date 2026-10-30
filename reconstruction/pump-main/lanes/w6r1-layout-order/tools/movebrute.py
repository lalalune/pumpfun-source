import sys,json,re
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
base=M.eval(M.cst)
movers=[M.pair[s] for s in M.UN]+[a for a in M.cst if a not in M.inv]
best=[]
for u in movers:
    o=[a for a in M.cst if a!=u]
    top=(0,None)
    for i in range(1,len(o)):
        if M.region(o[i-1])!='L': continue
        r=M.eval(o[:i]+[u]+o[i:])
        if len(r)>top[0]: top=(len(r),i,len(r-base),len(base-r))
    print(hex(u),M.names[u][:70],'best',top[0],top[2:], 'after', M.names[o[top[1]-1]][:80] if top[1] else None)
