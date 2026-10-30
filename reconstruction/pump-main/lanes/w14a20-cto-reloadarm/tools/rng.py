#!/usr/bin/env python3
import sys
f,lo,hi=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
for l in open(f):
    a=int(l.split()[0],16)
    if lo<=a<=hi: print(l.rstrip())
