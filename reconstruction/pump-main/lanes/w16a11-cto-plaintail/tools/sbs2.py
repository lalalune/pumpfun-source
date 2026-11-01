#!/usr/bin/env python3
"""sbs2.py <fn.bin> lo hi: L2-aligned side by side of orig [lo,hi) vs candidate (disassembly), marking register/frame diffs."""
import sys,os,difflib,types
T=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'t84')
C=types.ModuleType('C'); _s=open(T+'/cls.py').read(); C.__dict__['__file__']=T+'/cls.py'; exec(_s[:_s.index('def main')],C.__dict__)
sys.path.insert(0,os.path.join(os.path.dirname(T),'t2')); import bdis
O=open(os.path.join(os.path.dirname(T),'orig.bin'),'rb').read(); c=open(sys.argv[1],'rb').read(); lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
def toks(raw,l): return [C.mask(t,l) for _,t in C.insns(raw)]
oi=C.insns(O); ci=C.insns(c); od=dict(bdis.d(O)); cd=dict(bdis.d(c))
sm=difflib.SequenceMatcher(None,toks(O,2),toks(c,2),autojunk=False)
o1=toks(O,1); c1=toks(c,1); o0=toks(O,0); c0=toks(c,0)
for tag,a1,a2,b1,b2 in sm.get_opcodes():
    if a2<=a1 and not (lo<=ci[b1][0] if b1<len(ci) else False): pass
    if a1<len(oi) and oi[min(a1,len(oi)-1)][0]>=hi: break
    if a2>a1 and oi[a2-1][0]<lo: continue
    n=max(a2-a1,b2-b1)
    for k in range(n):
        a=a1+k if a1+k<a2 else None; b=b1+k if b1+k<b2 else None
        ol=f'{oi[a][0]:05x} {od[oi[a][0]]}' if a is not None else ''
        cl=f'{ci[b][0]:05x} {cd[ci[b][0]]}' if b is not None else ''
        if a is not None and not (lo<=oi[a][0]<hi): continue
        mk=' ' if tag!='equal' else ('=' if o0[a]==c0[b] else ('f' if o1[a]==c1[b] else 'R'))
        if tag!='equal': mk='!'
        print(f'{mk} {ol:42s} | {cl}')
