#!/usr/bin/env python3
"""clones.py <m.ll>: list AccountInfo clone base values X (GEPs X+8,16,24,32,40,41,42 within 120 lines) in order."""
import sys,re
L=open(sys.argv[1]).read().split('\n')
for i,l in enumerate(L):
    m=re.match(r'  (%\S+) = getelementptr inbounds i8, ptr (%\S+), i64 8$',l)
    if not m: continue
    X=m.group(2); w='\n'.join(L[i:i+120])
    if all(re.search(r'getelementptr inbounds i8, ptr '+re.escape(X)+r', i64 '+str(o)+r'\n',w) for o in (16,24,32,40,41,42)):
        d=next((L[j] for j in range(i,0,-1) if L[j].startswith('  '+X+' = ')),'?')
        print(i,X,d.strip()[:110])
