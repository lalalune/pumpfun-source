import sys,difflib
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import ctoracle as co
otok,w=co.orig_tokens()
ctok,n=co.so_tokens(sys.argv[1])
def mreg(t):
    b=bytearray(t); d=b[1]&15; s=b[1]>>4
    if d!=10: d=0
    if s!=10 and s!=1 or b[0]!=0x85: 
        if s!=10: s=0
    b[1]=(s<<4)|d; return bytes(b)
def mregf(t): return co.abstract(mreg(t))
for name,f in [('plain',lambda t:t),('reg',mreg),('frame',co.abstract),('reg+frame',mregf)]:
    sm=difflib.SequenceMatcher(None,[f(t) for t in otok],[f(t) for t in ctok],autojunk=False)
    print(name,round(sm.ratio(),5))
