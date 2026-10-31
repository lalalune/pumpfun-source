#!/usr/bin/env python3
"""regchunk.py base.bin var.bin [lo hi] [--step 0x200]: align each fn against the original with frame+regs masked
(splice lvl2), then per orig chunk count aligned insns whose registers match the original (base vs var), and list the
dominant (orig reg -> cand reg) pairs that the var has and base does not, within [lo,hi)."""
import sys,difflib,collections,struct
from pathlib import Path
import importlib.util
T=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('splice',T/'splice.py'); sv=sys.argv; sys.argv=['x']
sp=importlib.util.module_from_spec(spec); spec.loader.exec_module(sp); sys.argv=sv
from score import original_windows
def toks(raw):
    out=[];i=0
    while i<len(raw):
        op=raw[i];n=16 if op==0x18 else 8;b=bytearray(raw[i:i+n])
        if op==0x85: b[1]&=0x0f;b[4:8]=b'\0'*4
        if op==0x18: b[4:8]=b'\0'*4;b[12:16]=b'\0'*4
        out.append((i,bytes(b)));i+=n
    return out
a=[x for x in sys.argv[1:] if not x.startswith('--')]
step=int(sys.argv[sys.argv.index('--step')+1],0) if '--step' in sys.argv else 0x200
if '--step' in sys.argv: a=[x for x in a if x!=hex(step) and x!=sys.argv[sys.argv.index('--step')+1]]
lo,hi=(int(a[2],0),int(a[3],0)) if len(a)>=4 else (0,1<<30)
O=toks([w for w in original_windows() if w['start']==0x22a10][0]['raw'])
def pairs(f):
    C=toks(open(f,'rb').read())
    sm=difflib.SequenceMatcher(None,[sp.mask(t,2) for _,t in O],[sp.mask(t,2) for _,t in C],autojunk=False)
    res={}
    for blk in sm.get_matching_blocks():
        for i in range(blk.size):
            (oo,x),(co,y)=O[blk.a+i],C[blk.b+i]; res[oo]=(x,y,co)
    return res
B=pairs(a[0]);V=pairs(a[1])
ch=collections.defaultdict(lambda:[0,0,0,0])
for oo,(x,y,_) in B.items(): ch[oo//step][0]+=1; ch[oo//step][1]+=(x[1]==y[1])
for oo,(x,y,_) in V.items(): ch[oo//step][2]+=1; ch[oo//step][3]+=(x[1]==y[1])
print('chunk  aligned(base) regok(base)  aligned(var) regok(var)  d_regok')
for k in sorted(ch):
    b=ch[k]
    if b[1]!=b[3] or b[0]!=b[2]: print('0x%05x %5d %5d   %5d %5d  %+d'%(k*step,b[0],b[1],b[2],b[3],b[3]-b[1]))
cb=collections.Counter();cv=collections.Counter()
for D,c in ((B,cb),(V,cv)):
    for oo,(x,y,_) in D.items():
        if not(lo<=oo<hi): continue
        for f,s in (('d',lambda v:v&15),('s',lambda v:v>>4)):
            if s(x[1])!=s(y[1]): c[('r%d'%s(x[1]),'r%d'%s(y[1]))]+=1
print('pairs in [%#x,%#x): var minus base'%(lo,min(hi,0xffffff)))
d=collections.Counter({k:cv[k]-cb[k] for k in set(cv)|set(cb)})
for k,v in sorted(d.items(),key=lambda kv:-abs(kv[1]))[:14]: print('  orig %s -> cand %s: base %d var %d (%+d)'%(k[0],k[1],cb[k],cv[k],v))
