#!/usr/bin/env python3
# rn.py <a> <b> [--step 0x400]: full-mask align two fn bins (a may be 'orig'), per region of a: reg rename counts a>b and frame rename counts
import sys,os,difflib,re
from collections import Counter
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
sys.path.insert(0,OUT+'/tools')
import dis as D
W=D.W
def L(n):
    if n=='orig':
        import oracle
        return list(D.dis(oracle.orig_window()))
    return list(D.dis(open(f'{OUT}/fx/{n}/fn.bin','rb').read()))
def ab(t):
    t=re.sub(r'\[r10 - 0x[0-9a-f]+\]','[FP]',t)
    t=re.sub(r'\br\d+\b','R',t)
    if t.startswith('j'): t=re.sub(r'[-+]0x[0-9a-f]+$','J',t)
    if t.startswith('call'): t='call'
    if t.startswith('lddw'): t=t.split(',')[0]
    return t
REG=[('E1',0,0x280),('E2',0x280,0x420),('E3',0x420,0x708),('V1',0x708,0xb00),('V2',0xb00,0xe60),('V3',0xe60,0x1258),('V4',0x1258,0x1490),('V5',0x1490,0x1800),('J1',0x1800,0x1990),('J2',0x1990,0x1c88),('W1',0x1c88,0x1f68),('S1',0x1f68,0x26e8),('T1',0x26e8,0x3c50),('C1',0x3c50,0x4aa8),('P1',0x4aa8,0x4e50),('EV',0x4e50,0x5558),('TL',0x5558,0x5a18),('S2',0x5a18,0x5c18),('W2',0x5c18,0x6b08)]
a,b=sys.argv[1],sys.argv[2]
A=L(a);B=L(b)
aa=[ab(t) for _,t in A]; bb=[ab(t) for _,t in B]
sm=difflib.SequenceMatcher(None,aa,bb,autojunk=False)
R={r[0]:Counter() for r in REG}; F={r[0]:Counter() for r in REG}; EQ=Counter(); N=Counter()
def rid(o):
    for r,l,h in REG:
        if l<=o<h: return r
for m in sm.get_matching_blocks():
    for k in range(m.size):
        oa,ta=A[m.a+k]; ob,tb=B[m.b+k]; r=rid(oa-W)
        N[r]+=1
        if ta==tb: EQ[r]+=1
        ra=re.findall(r'\br\d+\b',ta); rb=re.findall(r'\br\d+\b',tb)
        for x,y in zip(ra,rb):
            if x!=y and x!='r10': R[r][f'{x}>{y}']+=1
        fa=re.findall(r'\[r10 - (0x[0-9a-f]+)\]',ta); fb=re.findall(r'\[r10 - (0x[0-9a-f]+)\]',tb)
        for x,y in zip(fa,fb):
            if x!=y: F[r][f'{x}>{y}']+=1
for r,_,_ in REG:
    print(r,N[r],EQ[r],' '.join(f'{k}x{v}' for k,v in R[r].most_common(10)),'| F',' '.join(f'{k}x{v}' for k,v in F[r].most_common(6)))
