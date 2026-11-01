#!/usr/bin/env python3
import sys; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/tools'); import dis as D
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
for o,s in D.dis(open(sys.argv[1],'rb').read()):
    if lo<=o<hi: print(hex(o),s)
