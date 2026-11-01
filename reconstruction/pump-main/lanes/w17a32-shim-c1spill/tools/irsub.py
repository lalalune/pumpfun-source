#!/usr/bin/env python3
"""irsub.py <in.ll> <out.ll> old=new ...: in the admin_cto function, delete the defining line of each %old and replace
its uses with %new (models a source that reads the field once). Experiment only."""
import sys,re
src,dst=sys.argv[1],sys.argv[2]; subs=[a.split('=',1) for a in sys.argv[3:]]
L=open(src).read().split('\n'); out=[]; inf=False
for l in L:
    if l.startswith('define ') and 'admin_cto7execute' in l: inf=True
    if inf:
        skip=False
        for o,n in subs:
            if re.match(r'\s*%'+re.escape(o)+r' = ',l): skip=True; break
        if skip: continue
        for o,n in subs:
            l=re.sub(r'%'+re.escape(o)+r'(?![\w.$])','%'+n,l)
    if inf and l=='}': inf=False
    out.append(l)
open(dst,'w').write('\n'.join(out))
