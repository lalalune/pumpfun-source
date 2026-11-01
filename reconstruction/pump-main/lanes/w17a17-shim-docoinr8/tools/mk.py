#!/usr/bin/env python3
"""mk.py <name> <base> : build src/<name>.rs from src/<base>.rs applying E[name] from edits.py (exact, once, line count kept); LIB[name] edits lib.rs"""
import sys,os,runpy
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w17a17-shim-docoinr8')
G=runpy.run_path(OUT+'/tools/edits.py'); E=G['E']; LIB=G.get('LIB',{})
name=sys.argv[1]; base=sys.argv[2] if len(sys.argv)>2 else 'main'
s=open(f'{OUT}/src/{base}.rs').read(); n0=s.count('\n')
for a,b in E[name]:
    c=s.count(a); assert c==1,(name,c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,(name,'line count changed')
open(f'{OUT}/src/{name}.rs','w').write(s)
if name in LIB:
    l=open(f'{OUT}/src/main.lib.rs').read(); m0=l.count('\n')
    for a,b in LIB[name]:
        c=l.count(a); assert c==1,(name,'lib',c,a[:120]); l=l.replace(a,b)
    assert l.count('\n')==m0
    open(f'{OUT}/src/{name}.lib.rs','w').write(l)
print('wrote',name)
