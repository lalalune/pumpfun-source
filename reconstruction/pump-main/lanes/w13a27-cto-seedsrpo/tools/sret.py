#!/usr/bin/env python3
"""sret.py <fn.bin|orig> : sret-demotion slot sites (mov r1,r10; add r1,-X; ... call) in layout order + ranks vs orig."""
import sys,struct,os
sys.path.insert(0,os.path.dirname(__file__)); import oracle
def ins(raw):
    i=0;out=[]
    while i<len(raw):
        op,regs,off,imm=struct.unpack_from('<BBhi',raw,i); out.append((i,op,regs&15,regs>>4,off,imm)); i+=16 if op==0x18 else 8
    return out
def sites(raw):
    I=ins(raw);res=[]
    for k,(p,op,d,s,off,imm) in enumerate(I):
        if op==0x85:
            for b in range(k-1,max(k-8,0),-1):
                pb,opb,db,sb,ob,ib=I[b]
                if opb==0x07 and db==1 and I[b-1][1]==0xbf and I[b-1][2]==1 and I[b-1][3]==10:
                    x=-ib
                    if 0x6a0<=x<=0x8e0: res.append((p,x))
                    break
    return res
o=sites(oracle.orig_window()); 
c=sites(open(sys.argv[1],'rb').read())
ro={x:i for i,x in enumerate(sorted(x for _,x in o))}; rc={x:i for i,x in enumerate(sorted(x for _,x in c))}
print(len(o),len(c))
for (po,xo),(pc,xc) in zip(o,c): print(f'{po:#7x} {xo:#x} r{ro[xo]:2d} | {pc:#7x} {xc:#x} r{rc[xc]:2d} {"" if ro[xo]==rc[xc] else "<<"}')
