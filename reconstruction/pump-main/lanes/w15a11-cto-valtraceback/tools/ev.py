#!/usr/bin/env python3
"""ev.py <rxname>...: ratio/bytes + true-LCS rfj and --- totals, and rfj per-0x400 chunk deltas (orig 0x0-0x1800) vs main."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import oracle,xled
from fact import mk
from lcs import lcs
from lcschunk_m import matched_ops
O=oracle.orig_window(); ot,oo=xled.toks(O)
def load(p): return xled.load(p if (p=='main' or '.' in p) else f'{os.path.dirname(T)}/rx/{p}/fn.bin')
def stats(p):
    ct,_=xled.toks(load(p)); r={}
    for m in ('---','rfj'):
        f=mk(m[0]=='r',m[1]=='f',m[2]=='j'); r[m]=lcs(f(ot),f(ct))
    f=mk(1,1,1); ops=matched_ops(f(ot),f(ct)); ch={}
    for op,i,j in ops:
        if op=='=' and oo[i]<0x1800: ch[oo[i]//0x400]=ch.get(oo[i]//0x400,0)+1
    r['ch']=ch; return r
base=stats('main')
print('main',base['---'],base['rfj'],' '.join(f'{k*0x400:x}:{v}' for k,v in sorted(base['ch'].items())))
for p in sys.argv[1:]:
    try: res=json.load(open(f'{os.path.dirname(T)}/rx/{p}/res.json'))
    except Exception: res={}
    s=stats(p); d=' '.join(f'{k*0x400:x}:{s["ch"].get(k,0)-v:+d}' for k,v in sorted(base['ch'].items()) if s['ch'].get(k,0)!=v)
    print(f"{p:18s} r={res.get('ratio')} B={res.get('bytes')} sd={res.get('slots_diff')} eq={res.get('eq_main')} L---={s['---']-base['---']:+d} Lrfj={s['rfj']-base['rfj']:+d} val[{d}]",flush=True)
