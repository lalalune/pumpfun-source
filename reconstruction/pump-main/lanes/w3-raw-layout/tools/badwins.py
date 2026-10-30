import sys,re; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-raw-layout/scripts')
from m13 import *
M=model(sys.argv[1],sys.argv[2]); cand=open(sys.argv[1],'rb').read(); o,c=M.osec,M.csec
for st,a,calls,tl,hd in M.checks:
    if not hd: continue
    oo=C.operands(M.wins[st]['raw'],st,o); co=C.operands(C.body(cand,c,a,M.units[a][0]),a,c)
    d=[(x,y) for x,y in zip(oo,co) if x[1]=='lddw' and x[3]!='.text']
    bads=[(x[3],hex(x[2]-o[x[3]]['addr']),y[3],hex(y[2]-c[y[3]]['addr'])) for x,y in d if not (x[3]==y[3] and x[2]-o[x[3]]['addr']==y[2]-c[y[3]]['addr'])]
    if bads: print(hex(st),re.sub(r'17h[0-9a-f]{16}E$','',M.names[a])[:80],bads[:4])
