import sys,json
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
R={a:M.region(a) for a in M.cst}
fix=lambda a: M.wins[M.inv[a]]['bytes'] if a in M.inv and M.inv[a] in M.UN else M.units[a][0]
def srt(reg): 
    xs=[a for a in M.cst if R[a]==reg]; return sorted(xs,key=lambda a:M.inv.get(a,1<<40))
def keep(reg): return [a for a in M.cst if R[a]==reg]
base=M.eval(M.cst)
for nm,o in [('Lorig',keep('U')+srt('L')+keep('D')),('Uorig',srt('U')+keep('L')+keep('D')),('Dorig',keep('U')+keep('L')+srt('D')),('UL',srt('U')+srt('L')+keep('D')),('all',srt('U')+srt('L')+srt('D'))]:
    r=M.eval(o); r2=M.eval([a for a in o if a in M.inv],fix)
    print(nm,'now-sizes',len(r),'+',sorted(hex(x) for x in r-base)[:40],'-',sorted(hex(x) for x in base-r),' | fixed-sizes',len(r2))
print('regions sizes',{k:sum(1 for a in M.cst if R[a]==k) for k in 'ULD'}, hex(M.lstart),hex(M.mend))
