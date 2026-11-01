#!/usr/bin/env python3
"""mk.py <name>...: build $OUT/src/<name>.rs from MKBASE (default m0) applying VARIANTS[name]=[(lineno,old,new),...].
Asserts each old occurs once on its line and the line count is unchanged."""
import sys,os
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w17a23-shim-rawfirst')
sys.path.insert(0,OUT+'/tools'); from variants import VARIANTS
def build(name):
    src=open(OUT+'/src/'+os.environ.get('MKBASE','m0')+'.rs').read().split('\n'); n=len(src)
    for ln,old,new in VARIANTS[name]:
        l=src[ln-1]; assert l.count(old)==1,(name,ln,old[:80],l.count(old)); src[ln-1]=l.replace(old,new)
    assert len(src)==n
    open(OUT+'/src/%s.rs'%name,'w').write('\n'.join(src))
if __name__=='__main__':
    for nm in sys.argv[1:]: build(nm); print('built',nm)
