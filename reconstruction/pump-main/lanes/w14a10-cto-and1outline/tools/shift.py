#!/usr/bin/env python3
"""shift.py name: median (cand_off - orig_off) of aligned insns per 0x400 orig region (where the size difference sits)."""
import sys,os,re,difflib,statistics
sys.path.insert(0,os.path.dirname(__file__))
from slots import orig_dis,cand_dis
from pbk import norm
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
od=orig_dis(); ot=[norm(t) for _,t in od]
for n in sys.argv[1:]:
    cd=cand_dis(O+'/rx/%s/m.o'%n); ct=[norm(t) for _,t in cd]
    sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False); d={}
    for a,b,s in sm.get_matching_blocks():
        for i in range(s): d.setdefault(od[a+i][0]//0x400,[]).append(cd[b+i][0]-od[a+i][0])
    print(n,' '.join('%x:%+d'%(k*0x400,int(statistics.median(v))) for k,v in sorted(d.items()) if len(v)>8))
