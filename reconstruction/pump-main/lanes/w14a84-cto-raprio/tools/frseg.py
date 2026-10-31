#!/usr/bin/env python3
"""frseg.py a.o b.o [...]: per-0x800 orig region, tokens matched plain / reg-masked / frame+reg-masked (difflib over whole fn)."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../w12a02-cto-iroracle/scripts"))
import tail, ctoracle as co
OT=tail.OT; OFF=tail.OFF
def seg(ct,f):
    sm=difflib.SequenceMatcher(None,[f(t) for t in OT],[f(t) for t in ct],autojunk=False); d={}
    for a,b,s in sm.get_matching_blocks():
        for k in range(s): r=OFF[a+k]//0x800*0x800; d[r]=d.get(r,0)+1
    return d
rows=[]
for p in sys.argv[1:]:
    ct=tail.toks(p); rows.append((p,seg(ct,lambda t:t),seg(ct,co.abstract),seg(ct,lambda t: co.abstract(tail.regmask(t)))))
print('region  '+'  '.join(f'{os.path.basename(os.path.dirname(r[0])):>16}' for r in rows))
for r in range(0,0x6c00,0x800):
    print(f'{r:#06x}  '+'  '.join(f'{x[1].get(r,0):4d}/{x[2].get(r,0):4d}/{x[3].get(r,0):4d}' for x in rows))
