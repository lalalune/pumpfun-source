#!/usr/bin/env python3
"""reg8.py fn.bin...: matched orig instructions per 0x800 orig region (global difflib alignment) at L0 (plain), L1 (frame masked), L2 (+regs masked). Experiment only."""
import sys,os,difflib,types
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
C=types.ModuleType('C'); C.__dict__['__file__']=T+'/cls.py'; _s=open(T+'/cls.py').read(); exec(_s[:_s.index('def main')],C.__dict__)
O=open(os.path.join(T,'..','orig.bin'),'rb').read(); oi=C.insns(O)
def reg(c,l):
    ci=C.insns(c); a=[C.mask(t,l) for _,t in oi]; b=[C.mask(t,l) for _,t in ci]
    cnt=[0]*((len(O)>>11)+1)
    for bl in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        for k in range(bl.size): cnt[oi[bl.a+k][0]>>11]+=1
    return cnt
base=None
for p in sys.argv[1:]:
    c=open(p,'rb').read(); r=[reg(c,l) for l in (0,1,2)]
    print(f"{p[-40:]:40s} {len(c)} " + ' | '.join('L%d %4d: '%(l,sum(r[l]))+' '.join('%3d'%x for x in r[l]) for l in (0,1,2)))
