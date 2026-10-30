#!/usr/bin/env python3
"""remap.py <fn.bin> <lo> <hi> <slo> <shi> <delta>: what-if: in fn bytes [lo,hi), r10-relative offsets -X with slo<=X<=shi become -(X+delta); print ratio."""
import sys,os,struct
T=os.path.dirname(os.path.abspath(__file__)); src=open(T+'/rx.py').read(); g={}; exec(src.split("OUT=os.environ")[0],g)
b=bytearray(open(sys.argv[1],'rb').read()); lo,hi,slo,shi=[int(x,16) for x in sys.argv[2:6]]; d=int(sys.argv[6])
i=0;n=0
while i<len(b):
    op=b[i]; regs=b[i+1]; off=struct.unpack_from('<h',b,i+2)[0]
    isld=(op&7) in (1,) ; isst=(op&7) in (2,3)
    if lo<=i<hi and ((isld and (regs>>4)==10) or (isst and (regs&15)==10)) and slo<=-off<=shi:
        struct.pack_into('<h',b,i+2,off-d); n+=1
    i+=16 if op==0x18 else 8
r,sd=g['metric'](bytes(b),g['orig_window']())
print(n,'changed; ratio',round(r,5))
