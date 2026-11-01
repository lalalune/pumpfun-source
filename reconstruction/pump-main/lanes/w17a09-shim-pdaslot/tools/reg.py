#!/usr/bin/env python3
"""reg.py <name> [<name>...]: per-region matched tokens (orig-side attribution) for fx fn.bin's"""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
OUT=os.path.dirname(T)
R=[('E1',0x0),('E2',0x280),('E3',0x420),('V1',0x708),('V2',0xb00),('V3',0xe60),('V4',0x1258),('V5',0x1490),('J1',0x1800),('J2',0x1990),('W1',0x1c88),('S1',0x1f68),('T1',0x26e8),('C1',0x3c50),('P1',0x4aa8),('EV',0x4e50),('TL',0x5558),('S2',0x5a18),('W2',0x5c18),('END',0x6b08)]
def split(raw):
    i=0;o=[]
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; o.append(i); i+=n
    return o
ow=oracle.orig_window(); ot=oracle.mask(ow); oo=split(ow)
rows={}
for n in sys.argv[1:]:
    p=n if os.path.exists(n) else f'{OUT}/fx/{n}/fn.bin'
    raw=open(p,'rb').read(); ct=oracle.mask(raw)
    sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False)
    cnt={r[0]:0 for r in R}
    for b in sm.get_matching_blocks():
        for k in range(b.a,b.a+b.size):
            off=oo[k]
            for i in range(len(R)-1):
                if R[i][1]<=off<R[i+1][1]: cnt[R[i][0]]+=1; break
    rows[n]=(sum(cnt.values()),len(raw),cnt)
names=list(rows)
print('%-6s'%'reg'+''.join('%9s'%n[:9] for n in names))
for r,_ in R[:-1]:
    base=rows[names[0]][2][r]
    print('%-6s'%r+''.join(('%9d'%rows[n][2][r]) if i==0 else ('%+9d'%(rows[n][2][r]-base)) for i,n in enumerate(names)))
print('%-6s'%'M'+''.join('%9d'%rows[n][0] for n in names)); print('%-6s'%'B'+''.join('%9d'%rows[n][1] for n in names))
