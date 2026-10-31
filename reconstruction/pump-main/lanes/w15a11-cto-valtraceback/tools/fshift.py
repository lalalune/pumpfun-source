#!/usr/bin/env python3
"""fshift.py <cand> <lo_hex> <hi_hex> <delta>: bound oracle; add delta to every r10 offset (and r10 lea imm) in (lo,hi] (negative offs), print ratio."""
import sys,os,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
p=sys.argv[1]; lo=-int(sys.argv[2],16); hi=-int(sys.argv[3],16); d=int(sys.argv[4])
C=bytearray(xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin'))
i=0; lea={}
while i<len(C):
    op=C[i]; cl=op&7; n=16 if op==0x18 else 8
    dst=C[i+1]&15; src=C[i+1]>>4
    if op==0xbf and src==10: lea[dst]=i
    elif op==0x07 and dst in lea and lea[dst]==i-8:
        v=struct.unpack_from('<i',C,i+4)[0]
        if lo<v<=hi: struct.pack_into('<i',C,i+4,v+d)
        lea.pop(dst,None)
    else:
        if (cl==1 and src==10) or (cl in (2,3) and dst==10):
            v=struct.unpack_from('<h',C,i+2)[0]
            if lo<v<=hi: struct.pack_into('<h',C,i+2,v+d)
        lea.pop(dst,None)
    i+=n
r,sd=oracle.metric(bytes(C),oracle.orig_window()); print(p,'shift',sys.argv[2:],'ratio',round(r,5),'bytes',len(C))
