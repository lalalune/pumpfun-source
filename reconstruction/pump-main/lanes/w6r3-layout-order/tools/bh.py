import sys,re
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
fix=lambda a: M.wins[M.inv[a]]['bytes'] if a in M.inv and M.inv[a] in M.UN else M.units[a][0]
order=list(M.cst)
bh=[a for a in order if M.inv.get(a)==0x13b9b8][0]; cr=[a for a in order if M.inv.get(a)==0x138b20][0]
o2=[a for a in order if a!=bh]; o2.insert(o2.index(cr)+1,bh)
print('ours fixed',len(M.eval(order,fix)),'bh moved fixed',len(M.eval(o2,fix)),'bh moved today',len(M.eval(o2)))
