#!/usr/bin/env python3
"""pe.py <m.ll> <edits.py> <out.ll>: post-opt IR edits (EDITS list of exact (old,new) pairs, each must occur once). Oracle only."""
import sys,runpy
t=open(sys.argv[1]).read(); g=runpy.run_path(sys.argv[2])
for a,b in g['EDITS']:
    c=t.count(a); assert c==1,(c,a[:150]); t=t.replace(a,b)
open(sys.argv[3],'w').write(t)
