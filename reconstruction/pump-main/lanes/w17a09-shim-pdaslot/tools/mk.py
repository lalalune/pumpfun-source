#!/usr/bin/env python3
"""mk.py <name> <base> : build src/<name>.rs from src/<base>.rs applying EDITS[name] from edits.py (exact, once, line count kept)"""
import sys,os,runpy
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w17a09-shim-pdaslot')
E=runpy.run_path(OUT+'/tools/edits.py')['E']
name=sys.argv[1]; base=sys.argv[2] if len(sys.argv)>2 else 'main'
s=open(f'{OUT}/src/{base}.rs').read(); n0=s.count('\n')
for a,b in E[name]:
    c=s.count(a); assert c==1,(name,c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,(name,'line count changed')
open(f'{OUT}/src/{name}.rs','w').write(s); print('wrote',name)
