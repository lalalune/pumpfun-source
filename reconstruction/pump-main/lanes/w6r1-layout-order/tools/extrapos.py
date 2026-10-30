import sys,json,re
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
base=M.eval(M.cst)
er=[a for a in M.cst if M.names[a].startswith('_ZN14pump_recovered18v2_native_payments18ensure_rent_exempt17')][0]
o=[a for a in M.cst if a!=er]
res=[]
for i in range(len(o)+1):
    oo=o[:i]+[er]+o[i:]
    r=M.eval(oo); res.append((len(r),i,len(r-base),len(base-r)))
res.sort(reverse=True)
for n,i,gn,ls in res[:15]:
    print(n,'+',gn,'-',ls,'after',M.region(o[i-1]),hex(o[i-1]),M.names[o[i-1]][:90])
