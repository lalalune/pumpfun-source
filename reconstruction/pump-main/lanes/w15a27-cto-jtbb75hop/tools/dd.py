import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import xled
import dis as D
p,lo,hi=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
b=D.orig() if p=='orig' else xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
for o,s in D.d(b):
    if lo<=o<hi: print(f'{o:05x} {s}')
