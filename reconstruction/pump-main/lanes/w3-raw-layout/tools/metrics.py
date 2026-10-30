import sys,re,json; sys.path.insert(0,sys.argv[1]+'/scripts')
from m13 import *
M=model(sys.argv[2],sys.argv[3]); g=datamap(M,sys.argv[2])
order=list(M.cst)
R={a:M.region(a) for a in M.cst}
Lo=[a for a in M.cst if R[a]=='U']+sorted([a for a in M.cst if R[a]=='L'],key=lambda a:M.inv.get(a,1<<40))+[a for a in M.cst if R[a]=='D']
full=sorted([a for a in M.cst if a in M.inv],key=lambda a:M.inv[a])
res={'raw_model':len(M.eval(order)),'P13':p13(M,order),'P13_dataeq':p13real(M,order,g),'P13_Lorig':p13(M,Lo),'P13_Lorig_dataeq':p13real(M,Lo,g),
 'P13_full':p13(M,full),'P13_full_dataeq':p13real(M,full,g),'data_ok_windows':sum(1 for v in g.values() if v),'LIS_breaks':MV.order_stats(M,order),'aligned':aligned(M,order)[0]}
print(json.dumps(res))
