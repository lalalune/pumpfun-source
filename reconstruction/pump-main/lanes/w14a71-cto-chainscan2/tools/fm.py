#!/usr/bin/env python3
"""fm.py fn.bin...: ratio, frame-masked ratio (r10 offsets masked) and skeleton (r10 offsets + registers masked) vs orig."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
def toks(raw,fr=False,rg=False):
    out=[]
    for t in G['mask'](raw):
        t=bytearray(t); op=t[0]; cls=op&7; dst=t[1]&15; srcr=t[1]>>4
        if fr and cls in (1,2,3) and (dst==10 or srcr==10): t[2:4]=b'\0\0'
        if rg: t[1]=0
        out.append(bytes(t))
    return out
O=G['orig_window']()
for f in sys.argv[1:]:
    c=open(f,'rb').read(); r=[]
    for fr,rg in ((0,0),(1,0),(1,1)):
        r.append(round(difflib.SequenceMatcher(None,toks(O,fr,rg),toks(c,fr,rg),autojunk=False).ratio(),5))
    print(f,len(c),'ratio %.5f fm %.5f sk %.5f'%tuple(r))
