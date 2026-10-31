import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
import dis as D
p=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
C=oracle.orig_window() if p=='orig' else xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
for a,s in D.d(C):
    if lo<=a<hi: print(f'{a:05x} {s}')
