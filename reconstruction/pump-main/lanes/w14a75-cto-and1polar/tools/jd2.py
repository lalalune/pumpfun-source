#!/usr/bin/env python3
"""jd2.py bin: list every jump aligned (jump-masked) with orig whose offsets differ: orig src, orig dst, cand src, cand dst, delta."""
import sys,os,difflib,struct
sa=sys.argv[:]; sys.argv=['x','n']
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rx.py')).read().split('OUT=os.environ')[0])
def toks(raw):
    out=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; out.append((i,raw[i:i+n])); i+=n
    return out
def isj(b): op=b[0]; return (op&7) in (5,6) and op not in (0x85,0x95)
O=orig_window(); C=open(sa[1],'rb').read(); ot=toks(O); ct=toks(C)
def key(b):
    m=bytearray(mask(b)[0])
    if isj(b): m[2:4]=b'\0\0'
    return bytes(m)
sm=difflib.SequenceMatcher(None,[key(b) for _,b in ot],[key(b) for _,b in ct],autojunk=False)
lo=int(sa[2],16) if len(sa)>2 else 0; hi=int(sa[3],16) if len(sa)>3 else 1<<30
for bl in sm.get_matching_blocks():
    for k in range(bl.size):
        (oa,ob),(ca,cb)=ot[bl.a+k],ct[bl.b+k]
        if isj(ob) and ob[2:4]!=cb[2:4] and lo<=oa<hi:
            oo=struct.unpack('<h',ob[2:4])[0]; co=struct.unpack('<h',cb[2:4])[0]
            print('o %5x->%5x  c %5x->%5x  d %+d'%(oa,oa+8+oo*8,ca,ca+8+co*8,(co-oo)*8))
