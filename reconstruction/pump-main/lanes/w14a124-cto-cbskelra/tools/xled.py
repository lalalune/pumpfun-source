#!/usr/bin/env python3
"""xled.py <cand.so|fn.bin|m.o> [--min N]: extra-code ledger. Skeleton-masked (regs, frame offs, jump offs, lea imm, call imm)
difflib alignment of cand vs original admin_cto::execute. Unmatched runs are then cross-aligned against the other side's
unmatched pool to separate MOVED code (has a counterpart elsewhere) from ours-only / orig-only code."""
import sys,os,difflib,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle
sys.path.insert(0,os.path.join(os.path.dirname(T),'s12','tools')); import dis as D
def fmask(t):
    out=[]
    for x in t:
        x=bytearray(x); op=x[0]; cl=op&7
        if (cl==1 and (x[1]>>4)==10) or (cl in (2,3) and (x[1]&15)==10): x[2:4]=b'\0\0'
        x[1]=0
        if cl in (5,6) and op not in (0x85,0x95): x[2:4]=b'\0\0'
        if op in (0x07,0x87): x[4:8]=b'\0'*4
        out.append(bytes(x))
    return out
def load(p):
    if p=='main': p=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
    if p.endswith('.bin'): return open(p,'rb').read()
    return oracle.elf_fn(p,oracle.KEEP)
def toks(raw):
    t=oracle.mask(raw); offs=[];a=0
    for x in t: offs.append(a); a+=len(x)
    return t,offs
def disl(raw):
    return dict(D.d(raw))
def run(p,mn=2,show=True):
    O=oracle.orig_window(); C=load(p)
    ot,oo=toks(O); ct,co=toks(C); of=fmask(ot); cf=fmask(ct)
    sm=difflib.SequenceMatcher(None,of,cf,autojunk=False)
    oh=[0]*len(of); ch=[0]*len(cf)
    for b in sm.get_matching_blocks():
        for k in range(b.size): oh[b.a+k]=1; ch[b.b+k]=1
    # cross-align unmatched pools
    ou=[i for i in range(len(of)) if not oh[i]]; cu=[j for j in range(len(cf)) if not ch[j]]
    sm2=difflib.SequenceMatcher(None,[of[i] for i in ou],[cf[j] for j in cu],autojunk=False)
    om=set(); cm=set()
    for b in sm2.get_matching_blocks():
        if b.size>=3:
            for k in range(b.size): om.add(ou[b.a+k]); cm.add(cu[b.b+k])
    def runs(h,mv,offs,tk):
        r=[];cur=None
        for i in range(len(h)):
            if not h[i] and i not in mv:
                if cur and cur[1]==i: cur[1]=i+1
                else: cur=[i,i+1]; r.append(cur)
        return [(offs[a],offs[b-1]+len(tk[b-1]),b-a,a,b) for a,b in r]
    cr=runs(ch,cm,co,ct); orr=runs(oh,om,oo,ot)
    res={'skM':sum(oh),'ours_only_tok':sum(x[2] for x in cr),'orig_only_tok':sum(x[2] for x in orr),
         'ours_moved_tok':len(cm),'orig_moved_tok':len(om),'cand_bytes':len(C)}
    if show:
        print(res)
        cd=disl(C); od=disl(O)
        def ctx(i,tks,offs):
            # nearest matched neighbour index in other side for locating
            return
        # map cand index -> orig index via matching blocks for location
        cmap={}
        for b in sm.get_matching_blocks():
            for k in range(b.size): cmap[b.b+k]=b.a
        omap={v:k for k,v in cmap.items()}
        def near(i,m,n):
            for d in range(1,400):
                if i-d in m: return m[i-d]
                if i+d<n and i+d in m: return m[i+d]
            return None
        print('== OURS-ONLY runs (cand off, len tok, ~orig loc) ==')
        for s,e,n,a,b in cr:
            if n<mn: continue
            nb=near(a,cmap,len(cf)); loc=f'{oo[nb]:05x}' if nb is not None else '?'
            print(f'cand {s:05x}-{e:05x} n={n:3d} ~orig {loc}')
            for i in range(a,b): print('     ',f'{co[i]:05x}',cd.get(co[i],'?'))
        print('== ORIG-ONLY runs ==')
        for s,e,n,a,b in orr:
            if n<mn: continue
            nb=near(a,omap,len(of)); loc=f'{co[nb]:05x}' if nb is not None else '?'
            print(f'orig {s:05x}-{e:05x} n={n:3d} ~cand {loc}')
            for i in range(a,b): print('     ',f'{oo[i]:05x}',od.get(oo[i],'?'))
    return res
if __name__=='__main__':
    a=sys.argv[1:]; mn=2
    if '--min' in a: i=a.index('--min'); mn=int(a[i+1]); del a[i:i+2]
    q='--q' in a; a=[x for x in a if x!='--q']
    for p in a: r=run(p,mn,not q); print(p,r) if q else None
