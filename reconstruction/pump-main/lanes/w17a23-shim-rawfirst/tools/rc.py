#!/usr/bin/env python3
"""rc.py <name> [<name2> ...]: matched tokens per original region (Ghidra w17a01 regions) for each fx capture."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,dis
OUT=os.path.dirname(T)
REG=[('E1',0x0),('E2',0x280),('E3',0x420),('V1',0x708),('V2',0xb00),('V3',0xe60),('V4',0x1258),('V5',0x1490),('J1',0x1800),('J2',0x1990),('W1',0x1c88),('S1',0x1f68),('T1',0x26e8),('C1',0x3c50),('P1',0x4aa8),('EV',0x4e50),('TL',0x5558),('S2',0x5a18),('W2',0x5c18),('END',0x6b08)]
ow=oracle.orig_window(); oi=dis.split(ow); ot=oracle.mask(ow)
def reg(a):
    for i in range(len(REG)-1):
        if REG[i][1]<=a<REG[i+1][1]: return REG[i][0]
def per(name):
    p=name if os.path.exists(name) else f'{OUT}/fx/{name}/fn.bin'
    raw=open(p,'rb').read(); ct=oracle.mask(raw)
    sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False); c={r:0 for r,_ in REG[:-1]}
    for a,b,n in sm.get_matching_blocks():
        for k in range(n): c[reg(oi[a+k][0])]+=1
    return sum(c.values()),len(raw),c
if __name__=='__main__':
    names=sys.argv[1:]; res=[per(n) for n in names]
    print('%-6s'%'reg'+''.join('%9s'%n[:9] for n in names)+('  d(%s-%s)'%(names[1][:6],names[0][:6]) if len(names)>1 else ''))
    for r,_ in REG[:-1]:
        vals=[x[2][r] for x in res]
        print('%-6s'%r+''.join('%9d'%v for v in vals)+('   %+d'%(vals[1]-vals[0]) if len(vals)>1 else ''))
    print('%-6s'%'M'+''.join('%9d'%x[0] for x in res)); print('%-6s'%'B'+''.join('%9d'%x[1] for x in res))
