#!/usr/bin/env python3
"""remap.py <m.o> 'lo:hi:delta,...': rewrite cand frame offsets in [lo,hi] by +delta (bytes in r10-off), score. Upper bound estimator."""
import sys,struct,os,runpy
g={}; src=open(os.path.join(os.path.dirname(__file__),'rx.py')).read(); exec(src[:src.index("OUT=os.environ.get('RX_OUT'")],g)
fn=bytearray(g['elf_fn'](sys.argv[1],g['KEEP'])); orig=g['orig_window']()
rules=[tuple(int(x,16) if i<2 else int(x) for i,x in enumerate(r.split(':'))) for r in sys.argv[2].split(',')] if len(sys.argv)>2 and sys.argv[2] else []
i=0
while i<len(fn):
    op=fn[i]; n=16 if op==0x18 else 8
    dst=fn[i+1]&0xf; src=fn[i+1]>>4; off=struct.unpack_from('<h',fn,i+2)[0]
    cls=op&7
    base=None
    if cls in (1,) and src==10: base=True   # ldx
    if cls in (2,3) and dst==10: base=True  # st/stx
    if base and off<0:
        o=-off
        for lo,hi,d in rules:
            if lo<=o<=hi: struct.pack_into('<h',fn,i+2,-(o+d)); break
    i+=n
r,sd=g['metric'](bytes(fn),orig); print(round(r,5),sd)
