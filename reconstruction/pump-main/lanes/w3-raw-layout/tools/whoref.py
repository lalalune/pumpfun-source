# whoref.py cand.so refined.json <orig rodata off hex> [<cand rodata off hex>]
import sys; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-raw-layout/scripts')
from m13 import *
M=model(sys.argv[1],sys.argv[2])
cand=open(sys.argv[1],'rb').read()
oo=int(sys.argv[3],16); co=int(sys.argv[4],16) if len(sys.argv)>4 else None
ob=M.osec['.rodata']['addr']+oo
for st in sorted(M.wins):
    for o,k,v,*r in C.operands(M.wins[st]['raw'],st,M.osec):
        if k=='lddw' and v==ob: print('orig',hex(st),'+',hex(o),M.names.get(M.pair.get(st),'?')[:100])
if co is not None:
    cb=M.csec['.rodata']['addr']+co
    for a in M.cst:
        for o,k,v,*r in C.operands(C.body(cand,M.csec,a,M.units[a][0]),a,M.csec):
            if k=='lddw' and v==cb: print('cand',hex(a),'+',hex(o),M.names[a][:100])
