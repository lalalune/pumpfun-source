#!/usr/bin/env python3
"""cc.py a.bin b.bin [lvl]: cand-vs-cand L2 diff; prints non-equal opcodes of >=6 instructions (a off range -> b off range)."""
import sys,os,difflib,types
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
C=types.ModuleType('C'); C.__dict__['__file__']=T+'/cls.py'; _s=open(T+'/cls.py').read(); exec(_s[:_s.index('def main')],C.__dict__)
A=C.insns(open(sys.argv[1],'rb').read()); B=C.insns(open(sys.argv[2],'rb').read()); l=int(sys.argv[3]) if len(sys.argv)>3 else 2
sm=difflib.SequenceMatcher(None,[C.mask(t,l) for _,t in A],[C.mask(t,l) for _,t in B],autojunk=False)
for tg,a1,a2,b1,b2 in sm.get_opcodes():
    if tg!='equal' and max(a2-a1,b2-b1)>=6:
        print(tg, 'a %05x-%05x (%d)'%(A[a1][0] if a1<len(A) else -1, A[a2-1][0] if a2>a1 else -1, a2-a1), 'b %05x-%05x (%d)'%(B[b1][0] if b1<len(B) else -1, B[b2-1][0] if b2>b1 else -1, b2-b1))
