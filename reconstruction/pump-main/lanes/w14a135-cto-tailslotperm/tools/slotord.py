#!/usr/bin/env python3
"""slotord.py <cand> <orig_lo> <orig_hi>: for each aligned tail reload ldxdw rX,[r10-S] in orig [lo,hi), print the
orig slot and the cand slot, and in each blob the position of the last store to that slot before the reload and the
first store to it in the function, plus how many distinct store sites the slot has (slot sharing)."""
import sys,os,difflib,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
import dis as D
p=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
O=oracle.orig_window(); C=xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
ot,oo=xled.toks(O); ct,co=xled.toks(C); fa=xled.fmask(ot); fb=xled.fmask(ct)
def fr(t):
    op=t[0]; cl=op&7
    if cl==1 and (t[1]>>4)==10 and (op&0x18)==0x18: return struct.unpack_from('<h',t,2)[0],'ld'
    if cl in(2,3) and (t[1]&15)==10 and (op&0x18)==0x18: return struct.unpack_from('<h',t,2)[0],'st'
    return None
def stores(toks,offs):
    s={}
    for t,o in zip(toks,offs):
        f=fr(t)
        if f and f[1]=='st': s.setdefault(f[0],[]).append(o)
    return s
so=stores(ot,oo); sc=stores(ct,co)
def last(s,off,pos):
    l=[x for x in s.get(off,[]) if x<pos]; return l[-1] if l else None
od=dict(D.d(O)); cd=dict(D.d(C))
print('opos  oslot  o_lastst o_nst | cpos  cslot  c_lastst c_nst  next-store')
for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,fa,fb,autojunk=False).get_opcodes():
    if tag!='equal': continue
    for k in range(i2-i1):
        i=i1+k; j=j1+k
        if not(lo<=oo[i]<hi): continue
        x=fr(ot[i]); y=fr(ct[j])
        if not(x and y and x[1]=='ld'): continue
        nx=od.get(oo[i+1],'')
        ol=last(so,x[0],oo[i]); cl=last(sc,y[0],co[j])
        print(f'{oo[i]:05x} {-x[0]:#06x} {ol if ol is None else hex(ol):>8} {len(so.get(x[0],[]))} | {co[j]:05x} {-y[0]:#06x} {cl if cl is None else hex(cl):>8} {len(sc.get(y[0],[]))} {"=" if x[0]==y[0] else "*"} {nx}')
