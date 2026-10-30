#!/usr/bin/env python3
"""cover.py a b [bucket]: per-bucket (orig instr index) matched-token coverage, abstracted tokens; prints buckets that differ."""
import sys,difflib,runpy
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a28-cto-entrycopy2'
sys.argv_s=sys.argv; g=runpy.run_path(O+'/tools/absr.py',run_name='lib') if False else None
src=open(O+'/tools/absr.py').read(); src=src[:src.index('for n in sys.argv')]
g={}; exec(src,g)
def cov(n,abs_=True):
    p=O+'/rx/'+n+'/fn.bin'; raw=open(p,'rb').read()
    c=g['toks'](raw) if abs_ else g['g']['mask'](raw)
    o=g['orig'] if abs_ else g['g']['mask'](g['g']['orig_window']())
    m=difflib.SequenceMatcher(None,o,c,autojunk=False)
    v=[0]*len(o)
    for a,b,s in m.get_matching_blocks():
        for i in range(a,a+s): v[i]=1
    return v
B=int(sys.argv[3]) if len(sys.argv)>3 else 64
for mode in (True,False):
    va,vb=cov(sys.argv[1],mode),cov(sys.argv[2],mode)
    print('abs' if mode else 'raw', sum(va), sum(vb))
    for i in range(0,len(va),B):
        x,y=sum(va[i:i+B]),sum(vb[i:i+B])
        if abs(x-y)>=4: print('  orig 0x%05x: %d -> %d (%+d)'%(0x22a10+i*8,x,y,y-x))
