#!/usr/bin/env python3
"""price.py <ref fn.bin> <out.jsonl> <cand.bin>...: per-region true-LCS matched original tokens (rapidfuzz LCSseq
alignment) for exact tokens and for the rfj mask (registers, frame offsets, jump offsets masked), candidate minus
reference, on the w17a01 region map (w17a14 rc.py REG). Experiment only."""
import sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import rc
from rapidfuzz.distance import LCSseq
O=rc.orig_window(); ot,oo=rc.mask(O)
def ids(toks,tab):
    return [tab.setdefault(t,len(tab)) for t in toks]
def per(ct,m):
    if m: A=rc.rfj(ot,True,True,True); B=rc.rfj(ct,True,True,True)
    else: A=ot; B=ct
    tab={}; a=ids(A,tab); b=ids(B,tab)
    d={}; tot=0
    for op in LCSseq.opcodes(a,b):
        if op.tag=='equal':
            for i in range(op.src_start,op.src_end):
                r=rc.reg_of(oo[i]); d[r]=d.get(r,0)+1; tot+=1
    return tot,d
ref=open(sys.argv[1],'rb').read(); rt,_=rc.mask(ref)
R0=per(rt,''); F0=per(rt,'rfj')
out=open(sys.argv[2],'a')
for p in sys.argv[3:]:
    c=open(p,'rb').read(); ct,_=rc.mask(c)
    e=per(ct,''); f=per(ct,'rfj')
    de={k:e[1].get(k,0)-R0[1].get(k,0) for _,k in rc.REG}; df={k:f[1].get(k,0)-F0[1].get(k,0) for _,k in rc.REG}
    rec={'id':os.path.basename(p)[:-4],'bytes':len(c),'lcs':e[0]-R0[0],'rfj':f[0]-F0[0],
         'reg':{k:v for k,v in de.items() if v},'regf':{k:v for k,v in df.items() if v}}
    out.write(json.dumps(rec)+'\n'); out.flush()
