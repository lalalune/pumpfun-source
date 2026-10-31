#!/usr/bin/env python3
"""renum.py <m.ll> <mn.ll>: rename numbered locals/labels of admin_cto7execute to %vN so lines can be moved."""
import sys,re
L=open(sys.argv[1]).read().split('\n'); out=[]; inf=False
for l in L:
    if l.startswith('define ') and 'admin_cto7execute' in l: inf=True
    if inf:
        l=re.sub(r'%(\d+)\b',r'%v\1',l)
        l=re.sub(r'^(\d+):',r'v\1:',l)
        if l=='}': inf=False
    out.append(l)
open(sys.argv[2],'w').write('\n'.join(out))
