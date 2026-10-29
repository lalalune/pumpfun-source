#!/usr/bin/env python3
"""applyp.py <patch.py> <srcdir>: patch.py defines P=[(file,old,new),...]"""
import sys,runpy
P=runpy.run_path(sys.argv[1])['P']; d=sys.argv[2]
for f,o,n in P:
    p=d+'/src/'+f; s=open(p).read()
    assert s.count(o)==1,('count',s.count(o),f,o[:100]); s=s.replace(o,n); open(p,'w').write(s)
