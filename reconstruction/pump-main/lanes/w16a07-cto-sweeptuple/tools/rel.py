#!/usr/bin/env python3
"""rel.py <dis> <base_hex> <lo_hex> <hi_hex>: print listing lines with function-relative offsets in [lo,hi)."""
import sys
f,base,lo,hi=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16),int(sys.argv[4],16)
for l in open(f):
    p=l.split(None,1)
    if not p or not p[0].startswith('0x'): continue
    a=int(p[0],16)-base
    if lo<=a<hi: print(f'{a:04x}  {p[1].rstrip()}')
