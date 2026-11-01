#!/usr/bin/env python3
"""splcheck.py <idx.npz> <pairs.json> [--n N]: exact-price the ranked splices and flag non-functions: exact difflib M,
splice bytes, call count (orig 157) and the multiset of 32-bit store/mov immediates in 1..2000 (error line numbers)
compared with the original's (duplicated or dropped error sites show up here)."""
import sys,os,json,difflib,struct
from collections import Counter
import numpy as np
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,xled
from regs import reg
LANES=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes')
O=oracle.orig_window(); OT,OO=xled.toks(O); N=len(OT)
def full(s):
    if s.endswith('.so'): return os.path.join(LANES,s)
    a,b=s.split('/',1); return os.path.join(LANES,a,'rx',b,'fn.bin')
def raw_toks(p):
    raw=open(p,'rb').read() if p.endswith('.bin') else oracle.elf_fn(p,oracle.KEEP)
    t=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; t.append(raw[i:i+n]); i+=n
    return t
def sig(rt):
    calls=sum(1 for x in rt if x[0]==0x85)
    lines=Counter()
    for x in rt:
        if x[0] in (0x62,0x7a,0xb7,0xb4):   # stw/stdw imm, mov imm
            v=struct.unpack('<i',x[4:8])[0]
            if 280<=v<=780: lines[v]+=1
    return calls,lines
OC,OL=sig(raw_toks(None) if False else [O[i:i+(16 if O[i]==0x18 else 8)] for i in range(0,len(O),8) if True][:0] or [])
def otoks():
    t=[];i=0
    while i<len(O):
        n=16 if O[i]==0x18 else 8; t.append(O[i:i+n]); i+=n
    return t
OC,OL=sig(otoks())
if __name__=='__main__':
    a=sys.argv[1:]; n=60
    if '--n' in a: i=a.index('--n'); n=int(a[i+1]); del a[i:i+2]
    Z=np.load(a[0]); names=[os.path.relpath(str(x),LANES).replace('/rx/','/').replace('/fn.bin','') for x in Z['names']]
    ix={s:i for i,s in enumerate(names)}; MP=Z['MP']
    rows=json.load(open(a[1]))[:n]; out=[]
    for r in rows:
        x=ix[r['front']]; y=ix[r['back']]; k=r['k']
        ra=raw_toks(full(r['front'])); rb=raw_toks(full(r['back']))
        c=ra[:MP[x][k]]+rb[MP[y][k]:]
        mt=[oracle.mask(t)[0] for t in c]
        M=sum(b.size for b in difflib.SequenceMatcher(None,OT,mt,autojunk=False).get_matching_blocks())
        b=sum(len(t) for t in c); calls,lines=sig(c)
        ld=sum(((lines-OL)+(OL-lines)).values())
        r.update(exactM=M,bytes=b,calls=calls,line_diff=ld,ok=(calls==OC and ld==0))
        out.append(r)
        print(f"{M:5d} {M-2249:+4d} est {r['estM']:5d} {b:6d}B calls {calls:3d} ld {ld:2d} {'OK ' if r['ok'] else 'BAD'} {r['orig']:#6x} {r['region']:12s} {r['front']} | {r['back']}",flush=True)
    json.dump(out,open(a[1].replace('.json','')+'.checked.json','w'),indent=0)
