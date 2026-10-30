#!/usr/bin/env python3
import sys,os,re
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
def seq(d):
    return [str(int(m.group(1),16)) for _,t in d for m in [re.match(r'stw \[r10 - 0x2[0-9a-f]{2}\], 0x([12][0-9a-f]{2})$',t)] if m][:12]
print('%-16s'%'orig',' '.join(seq(orig_dis())))
for p in sys.argv[1:]: print('%-16s'%p.split('/')[-2],' '.join(seq(cand_dis(p))))
