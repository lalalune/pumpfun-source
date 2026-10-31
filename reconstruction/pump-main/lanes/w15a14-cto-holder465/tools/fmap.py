#!/usr/bin/env python3
"""fmap.py <a.bin> <b.bin>: skeleton-align each against the original; for frame-offset instructions, per orig offset count
pairs whose cand offset equals orig (hit) in a and b; print offsets where hits differ."""
import sys,os,difflib,collections,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
O=oracle.orig_window(); ot,oo=xled.toks(O); of=xled.fmask(ot)
def fo(x):
    op=x[0]; cl=op&7
    if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): return struct.unpack('<h',x[2:4])[0]
    return None
def prof(p):
    C=open(p,'rb').read(); ct,co=xled.toks(C); cf=xled.fmask(ct)
    hit=collections.Counter(); tot=collections.Counter(); where=collections.defaultdict(list)
    for bl in difflib.SequenceMatcher(None,of,cf,autojunk=False).get_matching_blocks():
        for k in range(bl.size):
            a=ot[bl.a+k]; b=ct[bl.b+k]; f=fo(a)
            if f is None: continue
            tot[f]+=1; hit[f]+= (fo(b)==f)
            if fo(b)!=f: where[f].append((oo[bl.a+k],fo(b)))
    return hit,tot,where
ha,ta,wa=prof(sys.argv[1]); hb,tb,wb=prof(sys.argv[2])
rows=[]
for f in sorted(set(ta)|set(tb)):
    d=hb[f]-ha[f]
    if d: rows.append((d,f))
rows.sort()
for d,f in rows[:25]+[('..','')]+rows[-10:]:
    if d=='..': print('..'); continue
    print(f"orig off {f:6d} ({-f:#x})  hits a {ha[f]}/{ta[f]}  b {hb[f]}/{tb[f]}  d {d:+d}  b-miss sample {[(hex(o),c) for o,c in wb[f][:4]]}")
print('total hits a',sum(ha.values()),'b',sum(hb.values()))
