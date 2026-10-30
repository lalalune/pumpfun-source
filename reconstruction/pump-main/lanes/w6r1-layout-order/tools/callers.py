import sys; sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
orig=(C.BASE/'original.so').read_bytes(); cand=open(sys.argv[1],'rb').read()
for t in sys.argv[3:]:
    t=int(t,16); print('orig callers of',hex(t))
    for st in M.ost:
        for off,k,v,x in C.operands(M.wins[st]['raw'],st,M.osec):
            if k=='call' and v==t: print('  ',hex(st),hex(st+off),'paired',M.names.get(M.pair.get(st),'?')[:80])
    ca=M.pair.get(t); print('cand callers of',ca and hex(ca))
    for a in M.cst:
        for off,k,v,x in C.operands(C.body(cand,M.csec,a,M.units[a][0]),a,M.csec):
            if k=='call' and v in (ca,0x442e0): print('  ',hex(a),hex(v),M.names[a][:80])
