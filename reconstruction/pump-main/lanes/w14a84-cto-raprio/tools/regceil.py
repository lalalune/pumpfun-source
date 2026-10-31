#!/usr/bin/env python3
"""regceil.py fn.bin...: plain ratio, register-only-masked ratio (perfect colouring, frame offsets kept), L1 and L2.
regonly - plain = what a perfect register assignment would add at the same structure and frame. Experiment only."""
import sys,difflib,types,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
C=types.ModuleType('C'); C.__dict__['__file__']=T+'/cls.py'; _s=open(T+'/cls.py').read(); exec(_s[:_s.index('def main')],C.__dict__)
src=open(T+'/rx.py').read(); g={'__name__':'x'}; exec(src.split("OUT=os.environ")[0],g)
O=g['orig_window']()
def regonly(t):
    b=bytearray(C.mask(t,0)); b[1]=0; return bytes(b)
def toks(raw,f): return [f(t) for _,t in C.insns(raw)]
for p in sys.argv[1:]:
    c=open(p,'rb').read()
    r=[difflib.SequenceMatcher(None,toks(O,f),toks(c,f),autojunk=False).ratio() for f in (lambda t:C.mask(t,0),regonly,lambda t:C.mask(t,1),lambda t:C.mask(t,2))]
    print(p,len(c),'plain/regonly/L1/L2',[round(x,5) for x in r])
