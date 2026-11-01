#!/usr/bin/env python3
# ivmap.py <ssc a> <ssc b>: map spill intervals between two modules via aligned accesses in no-share code; print colour changes
import sys,os,re,difflib,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sscsim
oracle=sscsim.oracle
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
def toks(S):
    raw=S.ns; out=[]; meta=[]; i=0
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8; t=bytearray(raw[i:i+n])
        if op==0x85: t[1]&=0x0f; t[4:8]=b'\0'*4
        if op==0x18: t[4:8]=b'\0'*4; t[12:16]=b'\0'*4
        off=None
        if op in (0x79,0x7b,0x71,0x73,0x61,0x63,0x69,0x6b):
            load=op in (0x79,0x71,0x61,0x69)
            base=(raw[i+1]>>4) if load else (raw[i+1]&15)
            o=int.from_bytes(raw[i+2:i+4],'little',signed=True)
            if base==10 and o in S.ns_off: off=S.ns_off[o]; t[2:4]=b'\0\0'
        t[1]=0 if op not in () else t[1]  # mask regs
        out.append(bytes(t)); meta.append((i,off)); i+=n
    return out,meta
a=sscsim.Sim(sys.argv[1]); b=sscsim.Sim(sys.argv[2])
ta,ma=toks(a); tb,mb=toks(b)
sm=difflib.SequenceMatcher(None,ta,tb,autojunk=False)
V=collections.defaultdict(collections.Counter)
for bl in sm.get_matching_blocks():
    for x in range(bl.size):
        A=ma[bl.a+x][1]; B=mb[bl.b+x][1]
        if A is not None and B is not None: V[A][B]+=1
ka=a.colour(a.order); kb=b.colour(b.order)
used=set()
rows=[]
for r,s in enumerate(a.order):
    v=V.get(s)
    if not v:
        rows.append(f'{r:3d} SS#{s} w={a.W[s]:.5g} k{ka[s]} -> (no map)'); continue
    t=v.most_common(1)[0][0]; used.add(t)
    flag='' if ka[s]==kb[t] else ' *'
    rows.append(f'{r:3d} SS#{s} w={a.W[s]:.5g} k{ka[s]} -> SS#{t} w={b.W[t]:.5g} rank{b.rank[t]} k{kb[t]}{flag}'+(f' {dict(v)}' if len(v)>1 else ''))
print('\n'.join(rows))
print('only in b:',[(s,round(b.W[s],5),kb[s]) for s in b.order if s not in used])
