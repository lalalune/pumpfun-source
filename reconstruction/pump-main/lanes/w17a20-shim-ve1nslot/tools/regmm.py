#!/usr/bin/env python3
"""regmm.py <fn.bin>...: per-region matched original tokens, exact and fully masked (frame+regs+jumps), regions = w17a01 table."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(os.path.dirname(T),'tools12'))
import mmask, oracle
R=[('E1',0x0),('E2',0x280),('E3',0x420),('V1',0x708),('V2',0xb00),('V3',0xe60),('V4',0x1258),('V5',0x1490),('J1',0x1800),('J2',0x1990),('W1',0x1c88),('S1',0x1f68),('T1',0x26e8),('C1',0x3c50),('P1',0x4aa8),('EV',0x4e50),('TL',0x5558),('S2',0x5a18),('W2',0x5c18),('END',0x6b08)]
O=oracle.orig_window()
def offs(raw):
    o=[];i=0
    while i<len(raw):
        o.append(i); i+=16 if raw[i]==0x18 else 8
    return o
OO=offs(O)
def per(c,**k):
    a=mmask.toks(O,**k); b=mmask.toks(c,**k); sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    hit=[0]*len(a)
    for x,_,n in sm.get_matching_blocks():
        for q in range(x,x+n): hit[q]=1
    out={}
    for (nm,lo),(_,hi) in zip(R,R[1:]):
        out[nm]=sum(hit[q] for q,x in enumerate(OO) if lo<=x<hi)
    return out
if __name__=='__main__':
    P=sys.argv[1:]; ex=[per(open(p,'rb').read()) for p in P]; fm=[per(open(p,'rb').read(),frame=True,regs=True,jumps=True) for p in P]
    print('reg   '+'  '.join(('%s'%os.path.basename(os.path.dirname(p)))[:10].rjust(10)+' (fm)     ' for p in P))
    for nm,_ in R[:-1]:
        print(f'{nm:4s}  '+'  '.join(f'{e[nm]:10d} ({f[nm]:4d})    ' for e,f in zip(ex,fm)))
    print('TOT   '+'  '.join(f'{sum(e.values()):10d} ({sum(f.values()):4d})    ' for e,f in zip(ex,fm)))
