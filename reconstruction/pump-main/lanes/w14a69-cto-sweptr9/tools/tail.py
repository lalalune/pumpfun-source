#!/usr/bin/env python3
"""tail.py <fn.bin|.so|.o>... : ratio + tail (orig 0x4c00-0x6b08) token agreement.
 plain = tokens in matching blocks of the plain difflib (what ratio counts) inside the tail
 reg   = matched with regs masked; fr = frame+regs masked (abstract+regmask)."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"../../w12a02-cto-iroracle/scripts"))
import ctoracle as co
LO,HI=0x4c00,0x6b08
def regmask(t):
    b=bytearray(t); d=b[1]&15; s=b[1]>>4
    if d!=10: d=0
    if s!=10 and b[0]!=0x85: s=0
    b[1]=(s<<4)|d; return bytes(b)
def toks(p):
    if p.endswith('.so'): return co.so_tokens(p)[0]
    if p.endswith('.o'): return co.obj_tokens(p)[0]
    raw=open(p,'rb').read(); out=[]; i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; out.append(raw[i:i+n]); i+=n
    return out
OT,_=co.orig_tokens(); OFF=[];o=0
for t in OT: OFF.append(o); o+=len(t)
def cnt(f,ot,ct,lo=LO,hi=HI):
    sm=difflib.SequenceMatcher(None,[f(t) for t in ot],[f(t) for t in ct],autojunk=False)
    n=0;N=0
    for a,b,s in sm.get_matching_blocks():
        for k in range(s):
            N+=1
            if lo<=OFF[a+k]<hi: n+=1
    return n,N
def run(p):
    ct=toks(p); tot=sum(1 for x in OFF if LO<=x<HI)
    pl=cnt(lambda t:t,OT,ct); rg=cnt(regmask,OT,ct); fr=cnt(lambda t:co.abstract(regmask(t)),OT,ct)
    m=co.metrics(OT,ct,sum(len(t) for t in ct),27400)
    print(f"{p}: ratio {m['ratio']} slots {m.get('slots_diff')} bytes {m['bytes']} | tail {tot}: plain {pl[0]} reg {rg[0]} fr {fr[0]} | all plain {pl[1]} reg {rg[1]}")
if __name__=="__main__":
    for p in sys.argv[1:]: run(p)
def regions(p,seg=0x800):
    import collections
    ct=toks(p); sm=difflib.SequenceMatcher(None,OT,ct,autojunk=False); R=collections.Counter()
    for a,b,s in sm.get_matching_blocks():
        for k in range(s): R[OFF[a+k]//seg]+=1
    return R
