#!/usr/bin/env python3
import sys,os,re
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
def seq(d):
    r=[]
    for o,t in d:
        m=re.search(r', 0x([0-9a-f]+)$',t)
        if m and t.startswith(('stw','stdw','mov')):
            v=int(m.group(1),16)
            if 0x1700<=v<=0x1900: r.append('%x:%d'%(o,v))
    return r
print('orig',' '.join(x.split(':')[1] for x in seq(orig_dis())))
for p in sys.argv[1:]: print(p.split('/')[-2],' '.join(x.split(':')[1] for x in seq(cand_dis(p))))
