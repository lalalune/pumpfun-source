#!/usr/bin/env python3
"""objscore.py <obj>...: ratio/bytes/slots/eq_main for admin_cto::execute in an llc object (experiment only)."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); g={}; exec(src.split("OUT=os.environ")[0],g)
orig=g['orig_window']()
bs=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
mm=g['mask'](g['elf_fn'](bs,g['KEEP']))
import struct
def fixfs(c):
    b=bytearray(c); i=0
    while i<len(b):
        op=b[i]
        if op in (0x7b,0x73,0x6b,0x63,0x7a,0x72,0x6a,0x62) and (b[i+1]&0xf)==10:
            off=struct.unpack_from('<h',b,i+2)[0]
            if off>=0: struct.pack_into('<h',b,i+2,off-0x1000)
        i+=16 if op==0x18 else 8
    return bytes(b)
for p in sys.argv[1:]:
    c=fixfs(g['elf_fn'](p,g['KEEP'])); r,sd=g['metric'](c,orig)
    print(json.dumps({'o':p,'ratio':round(r,5),'bytes':len(c),'slots':sd,'eq_main':g['mask'](c)==mm}))
