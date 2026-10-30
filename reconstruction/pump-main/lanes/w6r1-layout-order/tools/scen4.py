import sys,json
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2]); g=datamap(M,sys.argv[1])
base=M.eval(M.cst)
r=M.eval(M.cst,data_ok=True); r=set(s for s in r if g[s])
print('cur order/sizes, text size forced equal, data offsets as built:',len(r))
er=[a for a in M.cst if 'ensure_rent_exempt' in M.names[a]][0]
o=[a for a in M.cst if a!=er]
r=M.eval(o,data_ok=True); r=set(s for s in r if g[s]); print('ensure_rent_exempt removed (callers unchanged size):',len(r))
# which units call ensure_rent_exempt
cand=open(sys.argv[1],'rb').read()
for a in M.cst:
    for off,k,v,x in C.operands(C.body(cand,M.csec,a,M.units[a][0]),a,M.csec):
        if k=='call' and v==er: print('caller',hex(a),M.inv.get(a) and hex(M.inv[a]),M.names[a][:90])
