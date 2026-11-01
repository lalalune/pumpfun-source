#!/usr/bin/env python3
"""regm.py <fn.bin> [<fn.bin> ...]: per-region matched-token counts (SequenceMatcher as fx.Mof), regions by original offset."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import oracle, fx
R=[('E1',0x0),('E2',0x280),('E3',0x420),('V1',0x708),('V2',0xb00),('V3',0xe60),('V4',0x1258),('V5',0x1490),('J1',0x1800),('J2',0x1990),('W1',0x1c88),('S1',0x1f68),('T1',0x26e8),('C1',0x3c50),('P1',0x4aa8),('EV',0x4e50),('TL',0x5558),('S2',0x5a18),('W2',0x5c18),('END',0x6b08)]
def offs(raw):
    o=[];i=0
    while i<len(raw):
        o.append(i); i+=16 if raw[i]==0x18 else 8
    return o
def per_region(b):
    O=fx.O(); c=oracle.mask(b); sm=difflib.SequenceMatcher(None,O,c,autojunk=False)
    oo=offs(oracle.orig_window()); hit=[0]*len(O)
    for a,_,n in sm.get_matching_blocks():
        for k in range(a,a+n): hit[k]=1
    out={}
    for (nm,lo),(_,hi) in zip(R,R[1:]):
        idx=[k for k,x in enumerate(oo) if lo<=x<hi]
        out[nm]=(sum(hit[k] for k in idx),len(idx))
    return out
if __name__=='__main__':
    rows=[(p,per_region(open(p,'rb').read())) for p in sys.argv[1:]]
    names=[r[0] for r in R[:-1]]
    print('region  orig  '+'  '.join(os.path.basename(os.path.dirname(p))[:12].rjust(12) for p,_ in rows))
    for nm in names:
        print(f"{nm:6s} {rows[0][1][nm][1]:5d}  "+'  '.join(str(d[nm][0]).rjust(12) for _,d in rows))
    print('TOTAL        '+'  '.join(str(sum(v[0] for v in d.values())).rjust(12) for _,d in rows))
