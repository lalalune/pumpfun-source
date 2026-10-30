#!/usr/bin/env python3
"""bfisites.py <prein.txt (print-before=inline dump of validate)> <bfi_val.txt> : to_string call sites -> error line, block, freq"""
import re,sys
L=open(sys.argv[1]).read().split('\n'); F={}
for m in re.finditer(r'- (\S+): float = ([\d.e-]+)',open(sys.argv[2]).read()): F[m.group(1)]=float(m.group(2))
blk='start'
for i,l in enumerate(L):
    m=re.match(r'^([\w.\-]+):',l)
    if m: blk=m.group(1)
    if 'ToString$GT$9to_string' in l and 'call' in l:
        ln=None
        for j in range(i,min(len(L),i+120)):
            mm=re.search(r'i32 (\d{3})\b',L[j])
            if mm and 280<=int(mm.group(1))<=340: ln=mm.group(1); break
        print(ln,blk,F.get(blk),'COLD' if F.get(blk,1)<0.02 else '')
