#!/usr/bin/env python3
"""abortjs.py <fn.bin|unstripped.so|orig>: list ja-target clusters (abort blocks) with >=5 incoming ja's."""
import sys,os,struct
from collections import defaultdict
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/w16-strategy/skeleton/tools')
import oracle
def load(p):
    if p=='orig': return oracle.orig_window()
    if p=='main': p=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
    if p.endswith('.so'): return oracle.elf_fn(p,oracle.KEEP)
    return open(p,'rb').read()
def ins(raw):
    out=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; out.append((i,raw[i:i+n])); i+=n
    return out
def clusters(raw):
    tg=defaultdict(list)
    for o,b in ins(raw):
        if b[0]==0x05:
            off=struct.unpack('<h',b[2:4])[0]; tg[o+8+8*off].append(o)
    return {t:v for t,v in tg.items() if len(v)>=5}
if __name__=='__main__':
    raw=load(sys.argv[1])
    for t,v in sorted(clusters(raw).items()):
        print(hex(t),len(v),[hex(x) for x in v][:30])
