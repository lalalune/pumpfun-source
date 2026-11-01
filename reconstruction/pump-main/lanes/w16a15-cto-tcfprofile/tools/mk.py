#!/usr/bin/env python3
"""mk.py <fn.bin>...: bytes, M, abort-jump profile (good of 41; TCF/sharing split), per-segment delta vs main,
and the c2 marker: dst register of the accounts+0xe8 Rc-pointer load (orig r6 at 0x3078) and of the skeleton-aligned
instructions at orig 0x3370 (orig r0 temps)."""
import sys,os,difflib,struct,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/w16-strategy/skeleton/tools')
import oracle,xled
from prof import rel
O=oracle.orig_window(); OT,OO=xled.toks(O); OF=xled.fmask(OT)
OM=oracle.mask(O)
MAIN=[8, 8, 8, 0, 0, -8, -8, 0, 0, -8, -8, 0, 0, 8, 8, 0, 32, 32, 8, 16, 32, 32, 24, 40, 40, 0, 0, 0, 0, 40, 40, 24, 24, 16, 24, -56, -64, -80, -80, -104, -40]
def seg(c): return [c[0]]+[c[i]-c[i-1] for i in range(1,len(c))]
def an(raw,probes=(0x3078,0x3370,0x33a0,0x30f0,0x31b0)):
    ct,co=xled.toks(raw); cf=xled.fmask(ct)
    M=sum(b.size for b in difflib.SequenceMatcher(None,OM,oracle.mask(raw),autojunk=False).get_matching_blocks())
    sm=difflib.SequenceMatcher(None,OF,cf,autojunk=False); pos={}
    for b in sm.get_matching_blocks():
        for k in range(b.size): pos[b.a+k]=b.b+k
    oidx={o:i for i,o in enumerate(OO)}
    mk={}
    for p in probes:
        i=oidx[p]; j=pos.get(i)
        mk[hex(p)]=None if j is None else ('r%d'%(ct[j][1]&15) if ct[j][0]!=0x7b else 'r%d'%(ct[j][1]>>4))
    # direct search: ldxdw rX,[rY+0xe8]
    e8=[ 'r%d@%x'%(t[1]&15,co[k]) for k,t in enumerate(ct) if t[0]==0x79 and struct.unpack('<h',t[2:4])[0]==0xe8 and 0x2600<=co[k]<0x3c00]
    d,t,js=rel(raw)
    r={'bytes':len(raw),'M':M}
    if d is not None:
        r.update({'good':sum(1 for x in d if x==0),'gt':sum(1 for x in d[:25] if x==0),'gs':sum(1 for x in d[25:] if x==0),
                  'dseg':[a-b for a,b in zip(seg(d),seg(MAIN))]})
    r['mk']=mk; r['e8']=e8
    return r
if __name__=='__main__':
    for f in sys.argv[1:]:
        raw=open(f,'rb').read() if not f.endswith('.so') else oracle.elf_fn(f,oracle.KEEP)
        r=an(raw); print(f.split('/rx/')[-1][:40],json.dumps(r))
