import sys; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-raw-layout/scripts')
from m13 import *
from collections import Counter
M=model(sys.argv[1],sys.argv[2]); cand=open(sys.argv[1],'rb').read(); o,c=M.osec,M.csec
bad=Counter(); badw=Counter(); n=0
for st,a,calls,tl,hd in M.checks:
    if not hd: continue
    oo=C.operands(M.wins[st]['raw'],st,o); co=C.operands(C.body(cand,c,a,M.units[a][0]),a,c)
    d=[(x,y) for x,y in zip(oo,co) if x[1]=='lddw' and x[3]!='.text']
    bads=[(x[3],x[2]-o[x[3]]['addr']) for x,y in d if not (x[3]==y[3] and x[2]-o[x[3]]['addr']==y[2]-c[y[3]]['addr'])]
    if bads:
        n+=1
        for s,off in set(bads): bad[(s,off//0x40*0x40)]+=1
print('windows with bad data',n)
for (s,off),k in sorted(bad.items()): print(s,hex(off),k)
