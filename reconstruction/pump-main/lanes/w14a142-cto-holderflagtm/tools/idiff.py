#!/usr/bin/env python3
# idiff.py <a.bin> <b.bin> [lo hi] : instruction-level diff (a offsets in [lo,hi))
import sys,difflib,os
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a142-cto-holderflagtm/t121'))
from bdis import decode
a=decode(open(sys.argv[1],'rb').read()); b=decode(open(sys.argv[2],'rb').read())
lo=int(sys.argv[3],0) if len(sys.argv)>3 else 0; hi=int(sys.argv[4],0) if len(sys.argv)>4 else 1<<30
import re
N=lambda s: re.sub(r'([+-])(0x[0-9a-f]+|\d+)(?=$)', r'\1J', s) if s.startswith(('j','ja')) else s
A=[N(x['txt']) for x in a]; B=[N(x['txt']) for x in b]
sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal' or i1>=len(a) or a[i1]['off']<lo or a[i1]['off']>=hi: continue
    print('%s A%05x(%d) B%05x(%d) | %s  =>  %s'%(op,a[i1]['off'],i2-i1,b[j1]['off'] if j1<len(b) else 0,j2-j1,' ; '.join(A[i1:min(i2,i1+4)]),' ; '.join(B[j1:min(j2,j1+4)])))
