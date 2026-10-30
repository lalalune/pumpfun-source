import sys,re,json; sys.path.insert(0,sys.argv[1]+'/scripts')
from m13 import *
M=model(sys.argv[2],sys.argv[3])
def byorig(lo,hi): return [a for a in M.cst if a in M.inv and lo<=M.inv[a]<=hi]
def place(order,units,anchor_orig=None,anchor_re=None,before=False):
    units=sorted(units,key=lambda a:M.inv[a]); s=set(units)
    rest=[a for a in order if a not in s]
    if anchor_orig is not None: anc=M.pair[anchor_orig]
    else: anc=[a for a in rest if re.search(anchor_re,M.names[a])][-1]
    i=rest.index(anc)+(0 if before else 1)
    return rest[:i]+units+rest[i:]
order=list(M.cst); print('base',p13(M,order),MV.order_stats(M,order),aligned(M,order))
steps=json.load(open(sys.argv[4]))
for name,lo,hi,anc,before in steps:
    order=place(order,byorig(int(lo,16),int(hi,16)),anchor_orig=int(anc,16),before=before)
    print(name,p13(M,order),MV.order_stats(M,order),'aligned',aligned(M,order),'now',len(M.eval(order)))
