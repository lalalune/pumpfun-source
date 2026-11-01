#!/usr/bin/env python3
"""relchk.py <unstripped.so>: .data.rel.ro word by word against the deployed ELF, pointers compared by section and by the refined function pairing."""
import sys,os,struct
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/relay/tools'))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import relay, mkorder2
from relaylib import demangle
t,c,sy,tf,tn,cn,pair0,idx=relay.compare(sys.argv[1])
P,left=mkorder2.refine(t,c,sy,tf,tn,cn)
dt,dc=t.sec['.data.rel.ro'],c.sec['.data.rel.ro']
rt,rc=t.sec['.rodata'],c.sec['.rodata']
bad=[];ok=0;nt=nr=nd=0
for off in range(0,min(dt['size'],dc['size']),8):
    at,ac=dt['addr']+off,dc['addr']+off
    wt=t.b[dt['off']+off:dt['off']+off+8];wc=c.b[dc['off']+off:dc['off']+off+8]
    a,b=at in t.rel,ac in c.rel
    if a!=b: bad.append((off,'reloc',a,b));continue
    if not a:
        if wt!=wc: bad.append((off,'plain',wt.hex(),wc.hex()))
        else: ok+=1
        continue
    vt,vc=t.ptr(at),c.ptr(ac)
    if t.ta<=vt<t.ta+t.tn:
        nt+=1
        if not c.ta<=vc<c.ta+c.tn or P.get(vt)!=vc: bad.append((off,'text',hex(vt),hex(vc),hex(P.get(vt,0)),demangle(sy.get(vc,(0,'?'))[1])[:60]))
        else: ok+=1
    elif rt['addr']<=vt<rt['addr']+rt['size']:
        nr+=1
        if vt-rt['addr']!=vc-rc['addr']: bad.append((off,'rodata',hex(vt-rt['addr']),hex(vc-rc['addr'])))
        else: ok+=1
    elif dt['addr']<=vt<dt['addr']+dt['size']:
        nd+=1
        if vt-dt['addr']!=vc-dc['addr']: bad.append((off,'data',hex(vt-dt['addr']),hex(vc-dc['addr'])))
        else: ok+=1
    else:
        bad.append((off,'other',hex(vt),hex(vc)))
print('words',dt['size']//8,'ok',ok,'bad',len(bad),'text ptrs',nt,'rodata ptrs',nr,'data ptrs',nd)
for x in bad[:40]: print(x)
