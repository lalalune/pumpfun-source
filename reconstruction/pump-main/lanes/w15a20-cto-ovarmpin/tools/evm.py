import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
from lcs import lcs
O=oracle.orig_window(); ot,oo=xled.toks(O)
def load(p): return xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
M=['---','r--','-f-','rf-','rfj']
def st(p):
    ct,_=xled.toks(load(p)); return [lcs(mk(m[0]=='r',m[1]=='f',m[2]=='j')(ot),mk(m[0]=='r',m[1]=='f',m[2]=='j')(ct)) for m in M]
b=st('main'); print('main',dict(zip(M,b)))
for p in sys.argv[1:]:
    s=st(p); print(f'{p:16s}',' '.join(f'{m}:{x-y:+d}' for m,x,y in zip(M,s,b)),flush=True)
