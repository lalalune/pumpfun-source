#!/usr/bin/env python3
"""objsc.py <obj>...: fixfs (SBF outgoing-arg bias) + px2 score; writes <obj>.bin"""
import sys,os,struct
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T+'/../t139'); import px2
def fixfs(c):
    b=bytearray(c); i=0
    while i<len(b):
        op=b[i]
        if op in (0x7b,0x73,0x6b,0x63,0x7a,0x72,0x6a,0x62) and (b[i+1]&0xf)==10:
            off=struct.unpack_from('<h',b,i+2)[0]
            if off>=0: struct.pack_into('<h',b,i+2,off-0x1000)
        i+=16 if op==0x18 else 8
    return bytes(b)
for f in sys.argv[1:]:
    c=fixfs(px2.G['elf_fn'](f,px2.G['KEEP'])) if not f.endswith('.bin') else open(f,'rb').read()
    if not f.endswith('.bin'): open(f[:-2]+'.bin','wb').write(c)
    s=px2.score_bin(c); print(f"{f:36s} ratio {s['ratio']:.5f} M {s['M']} bytes {s['bytes']}")
