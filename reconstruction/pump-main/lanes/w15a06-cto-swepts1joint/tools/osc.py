#!/usr/bin/env python3
"""osc.py <obj|bin>...: ratio, M, bytes (px2) and true-LCS rfj (w14a128 lcs) for admin_cto::execute"""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T+'/../t139'); import px2
sys.path.insert(0,T+'/../t128'); import oracle as o128, xled
from fact import mk
import lcs as L
for f in sys.argv[1:]:
    c=open(f,'rb').read() if f.endswith('.bin') else px2.G['elf_fn'](f,px2.G['KEEP'])
    if not f.endswith('.bin'): open(f.rsplit('.',1)[0]+'.bin','wb').write(c)
    s=px2.score_bin(c)
    print(f"{f:40s} ratio {s['ratio']:.5f} M {s['M']} bytes {s['bytes']}")
