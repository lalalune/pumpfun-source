#!/usr/bin/env python3
"""segall.py <cand> [--top N] [--ref <cand2>]: whole-function anchored (alignment-free) profile of admin_cto::execute.
Anchors: every call (0x85) and every Rc-overflow `ja` (the function's most common ja target). When orig and cand have the
same anchor count, segment k of orig is paired with segment k of cand and compared by difflib at mask levels
M (scorer), rM (regs masked), fM (frame masked), rfM, skM (xled skeleton). Totals are an alignment-free view: skM gaps are
code shape (ISel / block layout / extra or missing code), rfM-skM gaps are jump/lea/call immediates, M-rfM gaps are
register colouring and frame slots. --top lists the segments with the largest orig-only skeleton (code-shape) gaps."""
import sys,os,difflib,collections
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from segcmp import fm,rm,M,load
def anchors(raw):
    t,o=xled.toks(raw); m=oracle.mask(raw)
    tgt=lambda i:o[i]+8+8*int.from_bytes(t[i][2:4],'little',signed=True)
    js=[i for i in range(len(t)) if t[i][0]==0x05]
    common=collections.Counter(tgt(i) for i in js).most_common(1)[0][0]
    an=[i for i in range(len(t)) if t[i][0]==0x85 or (t[i][0]==0x05 and tgt(i)==common)]
    return t,m,o,an
def prof(p):
    Ot,Om,Oo,Oa=anchors(load('orig')); Ct,Cm,Co,Ca=anchors(load(p))
    if len(Oa)!=len(Ca): raise SystemExit(f'{p}: anchor count {len(Ca)} vs orig {len(Oa)}')
    bo=[-1]+Oa+[len(Ot)-1]; bc=[-1]+Ca+[len(Ct)-1]; rows=[]
    for k in range(len(bo)-1):
        sa=slice(bo[k]+1,bo[k+1]+1); sb=slice(bc[k]+1,bc[k+1]+1)
        a,b=Om[sa],Cm[sb]
        v=[M(a,b),M(rm(a),rm(b)),M(fm(a),fm(b)),M(rm(fm(a)),rm(fm(b))),M(xled.fmask(Ot[sa]),xled.fmask(Ct[sb]))]
        rows.append(dict(k=k,o=Oo[bo[k]+1] if bo[k]+1<len(Oo) else 0,c=Co[bc[k]+1] if bc[k]+1<len(Co) else 0,no=len(a),nc=len(b),v=v))
    return rows
if __name__=='__main__':
    a=sys.argv[1:]; top=0; ref=None
    if '--top' in a: i=a.index('--top'); top=int(a[i+1]); del a[i:i+2]
    if '--ref' in a: i=a.index('--ref'); ref=a[i+1]; del a[i:i+2]
    R=prof(a[0]); tot=[sum(r['v'][j] for r in R) for j in range(5)]
    print(f"{a[0]}: {len(R)} segments; anchored M/rM/fM/rfM/skM = {tot}; orig tokens {sum(r['no'] for r in R)}")
    if ref:
        Q=prof(ref); qt=[sum(r['v'][j] for r in Q) for j in range(5)]
        print(f"ref {ref}: {qt}; delta {[x-y for x,y in zip(tot,qt)]}")
        for r,q in zip(R,Q):
            d=[x-y for x,y in zip(r['v'],q['v'])]
            if any(d): print(f"  seg {r['k']:3d} o {r['o']:05x} c {r['c']:05x}/{q['c']:05x} n {r['no']}/{r['nc']}/{q['nc']} d {d}")
    if top:
        R2=sorted(R,key=lambda r:-(r['no']-r['v'][4]))
        for r in R2[:top]: print(f"  seg {r['k']:3d} o {r['o']:05x} c {r['c']:05x} n {r['no']:3d}/{r['nc']:3d} M/rM/fM/rfM/skM {r['v']} sk_gap {r['no']-r['v'][4]}")
