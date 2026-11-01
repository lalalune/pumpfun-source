#!/usr/bin/env python3
"""fuev.py <fn.bin>... : faithunion metrics per capture (experiment only, no build slot).
true LCS (exact / rfj / op) of the whole fn (w16-strategy collapse.py masks: call+lddw imm masked),
head rfj/exact (headcmp.py: orig 0x0-0x1c00 vs best variant cut), and a dotmap swap flag
(median shift of unique rfj 5-grams for orig chunks 0x2400-0x3c00 and 0x3c00-0x5400). Prints one JSON per line."""
import sys,json,os
from collections import defaultdict
_args=sys.argv[1:]; sys.argv=sys.argv[:1]
_src=open('/Users/shawwalters/.cache/pumpfun-reconstruction/w16-strategy/ceilings/collapse.py').read().split("O = toks(ws['raw'])")[0]
exec(_src)
O=toks(ws['raw'])
OA=[ab(t,'rfj') for t in O]; OE=[ab(t,'exact') for t in O]; OP=[ab(t,'op') for t in O]
def offs(T):
    o=[];p=0
    for t in T: o.append(p); p+=len(t)
    return o
oo=offs(O); OH=[i for i in range(len(O)) if oo[i]<0x1c00]
k=5
def dot(C):
    CA=[ab(t,'rfj') for t in C]; co=offs(C); idx=defaultdict(list)
    for j in range(len(CA)-k+1): idx[tuple(CA[j:j+k])].append(j)
    col={}
    for ch in range(0x2400,0x5400,0x400):
        hits=[]
        for i in range(len(OA)-k+1):
            if ch<=oo[i]<ch+0x400:
                js=idx.get(tuple(OA[i:i+k]),[])
                if len(js)==1: hits.append(co[js[0]]-oo[i])
        hits.sort(); col[ch]=hits[len(hits)//2] if hits else None
    return col
_T2=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'t2'); sys.path.insert(0,_T2)
import oracle as _or, xled as _xl
from fact import mk as _mk
from lcs import lcs as _blcs
_ot,_=_xl.toks(_or.orig_window())
def ev(path):
    raw=open(path,'rb').read(); C=toks(raw); co=offs(C)
    r={'f':path,'bytes':len(raw)}
    _ct,_=_xl.toks(raw)
    for m in ('---','rfj'):
        f=_mk(m[0]=='r',m[1]=='f',m[2]=='j'); r['L'+m]=_blcs(f(_ot),f(_ct))
    r['lcs_x'],r['lcs_rfj'],r['lcs_op']=[lcs([ab(t,l) for t in O],[ab(t,l) for t in C]) for l in ('exact','rfj','op')]
    r['bag4']=bag(OA,[ab(t,'rfj') for t in C])
    best=None
    for cut in range(0x1a00,0x2200,0x100):
        CH=[j for j in range(len(C)) if co[j]<cut]
        v=lcs([OA[i] for i in OH],[ab(C[j],'rfj') for j in CH])
        if best is None or v>best[0]: best=(v,cut,CH)
    r['head_rfj']=best[0]; r['head_x']=lcs([OE[i] for i in OH],[ab(C[j],'exact') for j in best[2]]); r['head_cut']=hex(best[1])
    d=dot(C); r['dot']={hex(a):(hex(b) if b is not None else None) for a,b in d.items()}
    r['swap']=any(b is not None and b<-0x800 for a,b in d.items() if a>=0x3c00)
    return r
if __name__=='__main__':
    for p in _args: print(json.dumps(ev(p)),flush=True)
