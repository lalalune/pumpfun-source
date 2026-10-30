import sys,re
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-raw-layout/scripts')
from m13 import *
from collections import Counter
M=model(sys.argv[1],sys.argv[2]); cand=open(sys.argv[1],'rb').read(); o,c=M.osec,M.csec
st=int(sys.argv[3],16); a=M.pair[st]
orig=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r1-layout-rodata/reconstruction/base/original.so','rb').read()
def show(b,S,ops,base):
    for x in ops:
        if x[1]=='lddw' and x[3]!='.text':
            off=x[2]-S[x[3]]['addr']; s=S[x[3]]; print('  ',hex(x[0]),x[3],hex(off),b[s['offset']+off:s['offset']+off+24])
print('orig'); show(orig,o,C.operands(M.wins[st]['raw'],st,o),st)
print('cand'); show(cand,c,C.operands(C.body(cand,c,a,M.units[a][0]),a,c),a)
