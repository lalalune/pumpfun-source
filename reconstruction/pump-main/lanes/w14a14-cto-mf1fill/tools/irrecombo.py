#!/usr/bin/env python3
"""irrecombo.py <m.ll> v1,v2,... : apply several re-read variants together (llc oracle) and print ratio/bytes/M."""
import sys,os,tempfile,difflib
sys.path.insert(0,os.path.dirname(__file__))
import irre_lib as I
m,vs=sys.argv[1],sys.argv[2].split(',')
t=open(m).read(); pre,fn,post=I.split_fn(t); O=I.orig()
for k,v in enumerate(vs):
    L,var=I.variants(fn,{v.split('@')[0]})
    var=[x for x in var if x[0]==v] or var
    fn=I.make(L,var[0],tag='c%d'%k)
r=I.run(pre,fn,post,O,tempfile.mkdtemp(prefix='combo'))
n=r['bytes']//8-88; r['M']=round(r['ratio']*(3339+n)/2,1); print(vs,r)
