import sys; sys.path.insert(0,sys.argv[1]+'/scripts')
from m13 import *
M=model(sys.argv[2],sys.argv[3])
R={a:M.region(a) for a in M.cst}
def reorder(regs):
    out=[]
    for r in 'ULD':
        u=[a for a in M.cst if R[a]==r]
        if r in regs: u=sorted([a for a in u if a in M.inv],key=lambda a:M.inv[a])+[a for a in u if a not in M.inv]
        out+=u
    return out
print('checks',len(M.checks),'official-model',len(M.eval(M.cst)))
for regs in ['','L','U','D','UL','LD','ULD']:
    print('P13',regs or 'ours',p13(M,reorder(regs)))
print('LIS/breaks',MV.order_stats(M,M.cst))
full=sorted([a for a in M.cst if a in M.inv],key=lambda a:M.inv[a])
print('P13 full orig',p13(M,full))
# region crossings
for a in M.cst:
    if a in M.inv:
        pass
ost=sorted(M.inv.values())
