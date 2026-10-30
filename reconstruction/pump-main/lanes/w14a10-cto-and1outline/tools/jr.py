#!/usr/bin/env python3
"""jr.py names..: scorer ratio, and the same with jump offsets masked (how much of the gap is jump distance)."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(__file__))
import oracle
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def jm(ws):
    out=[]
    for w in ws:
        op=w[0]
        if op&7 in (5,6) and op not in (0x85,0x95): w=w[:2]+b'\0\0'+w[4:]
        out.append(w)
    return out
if __name__!="__main__": pass
orig=oracle.mask(oracle.orig_window())
for n in sys.argv[1:]:
    c=oracle.mask(open(O+'/rx/%s/fn.bin'%n,'rb').read())
    r=difflib.SequenceMatcher(None,orig,c,autojunk=False).ratio()
    r2=difflib.SequenceMatcher(None,jm(orig),jm(c),autojunk=False).ratio()
    print('%-28s %d %.5f jm %.5f'%(n,len(c)*8,r,r2))
