#!/usr/bin/env python3
"""fmap.py cand...: for frame-masked matches vs orig, count (orig r10 off -> cand r10 off) pairs; print pairs where cand!=orig, per cand."""
import sys,os,difflib,struct,collections
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
O=oracle.orig_window()
def toks(b):
    out=[];i=0
    while i<len(b):
        n=16 if b[i]==0x18 else 8; out.append(b[i:i+n]); i+=n
    return out
def fm(x):
    x=bytearray(x); op=x[0]; cl=op&7
    if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): x[2:4]=b'\0\0'
    if op==0x07: x[4:8]=b'\0'*4
    return bytes(x)
def off(x):
    op=x[0]; cl=op&7
    if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): return struct.unpack_from('<h',x,2)[0]
    return None
ot=oracle.mask(O)
for p in sys.argv[1:]:
    q=p if '.' in p else f'{os.path.dirname(T)}/rx/{p}/fn.bin'
    c=oracle.mask(xled.load(q))
    sm=difflib.SequenceMatcher(None,[fm(x) for x in ot],[fm(x) for x in c],autojunk=False)
    cnt=collections.Counter(); good=collections.Counter()
    for m in sm.get_matching_blocks():
        for k in range(m.size):
            a,b=off(ot[m.a+k]),off(c[m.b+k])
            if a is None: continue
            if a!=b: cnt[(a,b)]+=1
            else: good[a]+=1
    print(p,'frame-mismatch',sum(cnt.values()),'match',sum(good.values()))
    globals().setdefault('R',{})[p]=cnt
if len(sys.argv)==3:
    a,b=R[sys.argv[1]],R[sys.argv[2]]
    keys=set(a)|set(b)
    for k in sorted(keys,key=lambda k:-(b.get(k,0)-a.get(k,0)))[:40]:
        if b.get(k,0)!=a.get(k,0): print('orig %6d -> cand %6d : %s %d  %s %d'%(k[0],k[1],sys.argv[1],a.get(k,0),sys.argv[2],b.get(k,0)))
