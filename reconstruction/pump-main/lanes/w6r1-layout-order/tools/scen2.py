import sys,json
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
ex=[a for a in M.cst if a not in M.inv]
print('extras',[(hex(a),M.units[a][0],M.names[a][:80]) for a in ex])
po=sorted(M.pair.items()); missing=[st for st in M.ost if st not in M.pair]
print('orig windows unpaired',[hex(x) for x in missing])
fix=lambda a: M.wins[M.inv[a]]['bytes'] if a in M.inv and M.inv[a] in M.UN else M.units[a][0]
base=M.eval(M.cst)
r1=M.eval(M.cst,fix); print('our order, unmatched fixed, extras kept',len(r1))
o2=[a for a in M.cst if a in M.inv]
r2=M.eval(o2,fix); print('..extras removed',len(r2))
nod={st for st,a,c,t,hd in M.checks if not hd}
print('nodata total',len(nod),'raw now',len(base&nod),'P8 nodata',len(r2&nod), 'P8 data-ok',len(M.eval(o2,fix,data_ok=True)))
full=sorted(o2,key=lambda a:M.inv[a])
print('full orig order, fixed',len(M.eval(full,fix,data_ok=True)))
# orig order but our sizes
print('full orig order, our sizes (nodata only)',len(M.eval(full)&nod), len(M.eval(full)))
