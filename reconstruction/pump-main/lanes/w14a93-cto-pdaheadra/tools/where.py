#!/usr/bin/env python3
"""where.py fn.bin lo hi: where does orig [lo,hi) (L2 tokens) sit in the candidate? local alignment of that slice vs the whole cand;
prints matching blocks (orig off -> cand off, size>=4)."""
import sys,os,difflib,types
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
C=types.ModuleType('C'); C.__dict__['__file__']=T+'/cls.py'; _s=open(T+'/cls.py').read(); exec(_s[:_s.index('def main')],C.__dict__)
O=open(os.path.join(T,'..','orig.bin'),'rb').read(); oi=C.insns(O)
c=open(sys.argv[1],'rb').read(); ci=C.insns(c); lo,hi=int(sys.argv[2],0),int(sys.argv[3],0)
oo=[(o,t) for o,t in oi if lo<=o<hi]
a=[C.mask(t,2) for _,t in oo]; b=[C.mask(t,2) for _,t in ci]
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
for bl in sm.get_matching_blocks():
    if bl.size>=4: print('orig %05x -> cand %05x  n=%d'%(oo[bl.a][0],ci[bl.b][0],bl.size))
