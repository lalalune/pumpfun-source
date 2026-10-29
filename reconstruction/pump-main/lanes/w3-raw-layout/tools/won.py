import sys,re; sys.path.insert(0,sys.argv[1]+'/scripts')
from m13 import *
M=model(sys.argv[2],sys.argv[3])
w=[a for a in M.cst if 'with_owned_name' in M.names[a]][0]
rest=[a for a in M.cst if a!=w]
idx=[i for i,a in enumerate(rest) if 'with_account_name' in M.names[a]]
print('wan group idx',idx,[hex(rest[i]) for i in idx])
for i in range(idx[0],idx[-1]+2):
    o=rest[:i]+[w]+rest[i:]
    print(i,'P13',p13(M,o),'now',len(M.eval(o)))
# ULD with w at orig
R={a:M.region(a) for a in M.cst}
full=sorted([a for a in M.cst if a in M.inv],key=lambda a:M.inv[a])
print('full',p13(M,full))
# U ours-order + w at  orig-correct slot? L,D original
U=[a for a in M.cst if R[a]=='U']; L=sorted([a for a in M.cst if R[a]=='L' and a!=w],key=lambda a:M.inv[a]); D=sorted([a for a in M.cst if R[a]=='D'],key=lambda a:M.inv[a])
best=max((p13(M,U[:i]+[w]+U[i:]+L+D),i) for i in range(len(U)+1)); print('U ours + best w slot + LD orig',best)
