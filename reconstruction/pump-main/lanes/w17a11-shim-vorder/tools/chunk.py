#!/usr/bin/env python3
"""chunk.py <a.bin> <b.bin> [chunk]: per original-chunk matched-token counts (difflib vs orig), a vs b."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,fx
def per(b,ch):
    o=fx.O(); c=oracle.mask(b); sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
    cnt={}
    for blk in sm.get_matching_blocks():
        for i in range(blk.a,blk.a+blk.size):
            k=(i*8)//ch; cnt[k]=cnt.get(k,0)+1
    return cnt
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read(); ch=int(sys.argv[3],16) if len(sys.argv)>3 else 0x800
A=per(a,ch); B=per(b,ch)
tot=0
for k in sorted(set(A)|set(B)):
    d=B.get(k,0)-A.get(k,0); tot+=d
    if d: print('%05x %4d %4d %+d'%(k*ch,A.get(k,0),B.get(k,0),d))
print('total',tot)
