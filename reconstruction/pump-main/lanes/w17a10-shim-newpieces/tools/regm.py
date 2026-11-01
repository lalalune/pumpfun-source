#!/usr/bin/env python3
"""regm.py <fn.bin>... : per-region matched original tokens (exact and reg/frame/jump-masked difflib alignment)."""
import sys,re,difflib
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/tools'); import dis as D
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/irbeam/tools'); import oracle
O=D.dis(oracle.orig_window())
REG={'E1':(0,0x280),'E2':(0x280,0x420),'E3':(0x420,0x708),'V':(0x708,0x1800),'J1':(0x1800,0x1990),'J2':(0x1990,0x1c88),'W1S1':(0x1c88,0x26e8),'T1':(0x26e8,0x3c50),'C1':(0x3c50,0x4aa8),'P1EV':(0x4aa8,0x5558),'tail':(0x5558,0x6b08)}
def norm(s):
    s=re.sub(r'call 0x[0-9a-f]+( \(int\))?','call X',s); s=re.sub(r'lddw (r\d), 0x[0-9a-f]+',r'lddw \1, L',s); return s
def mask(s,frame=True,reg=True,jmp=True):
    s=norm(s)
    if reg: s=re.sub(r'\br\d\b','r',s)
    if frame: s=re.sub(r'\[r10 [+-] 0x[0-9a-f]+\]','[fp]',s); s=re.sub(r'(add64 r\d*, )-0x[0-9a-f]+','\\1-F',s) if False else s
    if jmp: s=re.sub(r', [+-]0x[0-9a-f]+$','',s); s=re.sub(r'^ja [+-]0x[0-9a-f]+$','ja',s)
    return s
def run(path):
    B=D.dis(open(path,'rb').read())
    out={}
    for mode,kw in (('exact',dict(frame=False,reg=False,jmp=False)),('rfj',dict())):
        a=[mask(s,**kw) if mode!='exact' else norm(s) for _,s in O]; b=[mask(s,**kw) if mode!='exact' else norm(s) for _,s in B]
        sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
        hit=[0]*len(O)
        for blk in sm.get_matching_blocks():
            for i in range(blk.a,blk.a+blk.size): hit[i]=1
        out[mode]={k:sum(hit[i] for i,(o,_) in enumerate(O) if lo<=o<hi) for k,(lo,hi) in REG.items()}
        out[mode]['ALL']=sum(hit)
    return out
tot={k:sum(1 for o,_ in O if lo<=o<hi) for k,(lo,hi) in REG.items()}
print('region  '+' '.join(f'{k:>6}' for k in list(REG)+['ALL']))
print('orig    '+' '.join(f'{tot[k]:>6}' for k in REG)+f' {len(O):>6}')
for p in sys.argv[1:]:
    r=run(p)
    for mode in ('exact','rfj'):
        print(f'{p.split("/")[-2][:10]:10} {mode[:3]} '+' '.join(f'{r[mode][k]:>6}' for k in list(REG)+['ALL']))
