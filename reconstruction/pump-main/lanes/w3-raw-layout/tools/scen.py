import sys,json
sys.path.insert(0,sys.argv[1])
import fastmodel as F
M=F.Model(sys.argv[2],sys.argv[3])
sc=json.load(open(sys.argv[4]))
off=set(int(k) for k,w in sc['windows'].items() if w['raw'])
base=M.eval(M.cst); print('model raw',len(base),'official',len(off),'diff',len(base^off))
R={a:M.region(a) for a in M.cst}
def reorder(regs):
    out=[]
    for r in 'ULD':
        u=[a for a in M.cst if R[a]==r]
        if r in regs:
            p=sorted([a for a in u if a in M.inv],key=lambda a:M.inv[a]); ex=[a for a in u if a not in M.inv]
            # keep extras at their position relative: append at end
            u=p+ex
        out+=u
    return out
for regs in ['L','U','D','UD','LD','UL','ULD']:
    r=M.eval(reorder(regs)); print(regs,len(r),'+',len(r-base),'-',len(base-r))
print('text size cand',hex(M.csec['.text']['size']),'orig',hex(M.osec['.text']['size']))
