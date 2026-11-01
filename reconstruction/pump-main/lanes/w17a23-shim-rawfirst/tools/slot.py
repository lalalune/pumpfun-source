#!/usr/bin/env python3
"""slot.py <name|fn.bin|orig> <off_hex> : list accesses to [r10 - off] with addresses (and region for orig)."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle, dis
OUT=os.path.dirname(T)
REG=[('E1',0x0),('E2',0x280),('E3',0x420),('V1',0x708),('V2',0xb00),('V3',0xe60),('V4',0x1258),('V5',0x1490),('J1',0x1800),('J2',0x1990),('W1',0x1c88),('S1',0x1f68),('T1',0x26e8),('C1',0x3c50),('P1',0x4aa8),('EV',0x4e50),('TL',0x5558),('S2',0x5a18),('W2',0x5c18),('END',0x6b08)]
def reg(a):
    for i in range(len(REG)-1):
        if REG[i][1]<=a<REG[i+1][1]: return REG[i][0]
    return '?'
def load(p):
    if p=='orig': return oracle.orig_window()
    if not os.path.exists(p): p=f'{OUT}/fx/{p}/fn.bin'
    return open(p,'rb').read()
if __name__=='__main__':
    p=sys.argv[1]; off=int(sys.argv[2],16)
    raw=load(p); out=[]
    for a,b in dis.split(raw):
        s=dis.dec(b)
        if f'r10 - {hex(off)}]' in s: out.append((a,s))
    from collections import Counter
    c=Counter(reg(a) for a,_ in out) if p=='orig' else None
    print(p,len(out),dict(c) if c else '')
    if '-v' in sys.argv:
        for a,s in out: print(' ',hex(a),reg(a) if p=='orig' else '',s)
