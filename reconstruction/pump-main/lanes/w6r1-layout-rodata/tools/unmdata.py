import sys,re
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-raw-layout/scripts')
from m13 import *
from collections import Counter
M=model(sys.argv[1],sys.argv[2]); cand=open(sys.argv[1],'rb').read(); o,c=M.osec,M.csec
orig=open(M.orig_path,'rb').read() if hasattr(M,'orig_path') else None
def rs(b,S,sec,off,n=48):
    s=S[sec]; return b[s['offset']+off:s['offset']+off+n]
for st in sorted(M.UN):
    a=M.pair.get(st)
    if a is None: print(hex(st),'unpaired'); continue
    oo=C.operands(M.wins[st]['raw'],st,o); co=C.operands(C.body(cand,c,a,M.units[a][0]),a,c)
    od=Counter((x[3],x[2]-o[x[3]]['addr']) for x in oo if x[1]=='lddw' and x[3]!='.text')
    cd=Counter((y[3],y[2]-c[y[3]]['addr']) for y in co if y[1]=='lddw' and y[3]!='.text')
    print(hex(st),M.names[a][:60],'orig',sum(od.values()),'cand',sum(cd.values()),'only-orig',dict((k[0]+':'+hex(k[1]),v) for k,v in (od-cd).items()),'only-cand',dict((k[0]+':'+hex(k[1]),v) for k,v in (cd-od).items()))
