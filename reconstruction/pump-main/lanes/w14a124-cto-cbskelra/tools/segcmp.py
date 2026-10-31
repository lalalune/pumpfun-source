#!/usr/bin/env python3
"""segcmp.py [--o lo:hi] [--c lo:hi] <cand>... : alignment-free clone-run comparison.
Splits orig and cand at the Rc-overflow anchors (each `ja` to the region's most common ja target, i.e. the shared
Rc-increment overflow panic) inside the given orig / cand ranges, pairs segment k with segment k, and sums per-pair difflib
matches at five mask levels: M (scorer mask), rM (regs masked), fM (frame offsets masked), rfM, skM (xled skeleton).
Compare with regM.py (matches inside the same orig range under the GLOBAL difflib alignment): when global skM << segment
skM, the global skeleton alignment is off-diagonal in that region (repetitive clone runs), and per-chunk skM deltas there are
alignment artifacts, not block moves. V=-v prints per-segment rows."""
import sys,os,difflib,collections
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
import dis as D
def fm(t):
    out=[]
    for x in t:
        x=bytearray(x); op=x[0]; cl=op&7
        if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): x[2:4]=b'\0\0'
        if op==0x07: x[4:8]=b'\0'*4
        out.append(bytes(x))
    return out
def rm(t): return [bytes([x[0],0])+x[2:] for x in t]
def jm(t): return [x[:2]+b'\0\0'+x[4:] if (x[0]&7) in (5,6) and x[0] not in (0x85,0x95) else x for x in t]
def M(a,b): return sum(k.size for k in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks())
def load(p): return oracle.orig_window() if p=='orig' else xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
def segs(raw,lo,hi):
    t,o=xled.toks(raw); m=oracle.mask(raw)
    tgt=lambda i:o[i]+8+8*int.from_bytes(t[i][2:4],'little',signed=True)
    js=[i for i,a in enumerate(o) if lo<=a<hi and t[i][0]==0x05]
    if not js: return t,m,o,[]
    common=collections.Counter(tgt(i) for i in js).most_common(1)[0][0]
    return t,m,o,[i for i in js if tgt(i)==common]
def main():
    a=sys.argv[1:]; orr=(0x3d00,0x4700); crr=None
    if '--o' in a: i=a.index('--o'); orr=tuple(int(x,16) for x in a[i+1].split(':')); del a[i:i+2]
    if '--c' in a: i=a.index('--c'); crr=tuple(int(x,16) for x in a[i+1].split(':')); del a[i:i+2]
    crr=crr or (orr[0]-0x100,orr[1])
    Ot,Om,Oo,Oa=segs(load('orig'),*orr); print('orig anchors',len(Oa))
    for p in a:
        Ct,Cm,Co,Ca=segs(load(p),*crr)
        if len(Ca)!=len(Oa): print(p,'anchor count',len(Ca),'(adjust --c)'); continue
        tot=[0]*5; rows=[]
        bo=[Oa[0]-40]+Oa; bc=[Ca[0]-40]+Ca
        for k in range(len(bo)-1):
            sa=slice(bo[k]+1,bo[k+1]+1); sb=slice(bc[k]+1,bc[k+1]+1)
            v=[M(Om[sa],Cm[sb]),M(rm(Om[sa]),rm(Cm[sb])),M(fm(Om[sa]),fm(Cm[sb])),M(rm(fm(Om[sa])),rm(fm(Cm[sb]))),M(xled.fmask(Ot[sa]),xled.fmask(Ct[sb]))]
            tot=[x+y for x,y in zip(tot,v)]; rows.append((Oo[bo[k]+1],Co[bc[k]+1],bo[k+1]-bo[k],bc[k+1]-bc[k],v))
        print(p,'segM/rM/fM/rfM/skM',tot,'orig tokens',bo[-1]-bo[0])
        if '-v' in os.environ.get('V',''):
            for r in rows: print('  ',f'{r[0]:05x} {r[1]:05x} n{r[2]:3d}/{r[3]:3d}',r[4])
if __name__=='__main__': main()
