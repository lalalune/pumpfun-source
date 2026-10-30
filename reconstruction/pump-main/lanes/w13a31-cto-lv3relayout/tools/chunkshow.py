#!/usr/bin/env python3
"""chunkshow.py label occ ann... : print chunk (lab,occ) from each annotated listing side by side (raw text)."""
import sys,collections
lab,occ=sys.argv[1],int(sys.argv[2])
for p in sys.argv[3:]:
    cur=[];c=collections.Counter()
    for l in open(p):
        l=l.rstrip('\n'); a,rest=l.split(None,1); cur.append(l)
        if ' call ' in ' '+rest or rest.strip()=='exit':
            lb=rest.split(';')[-1].strip()[:45] if ';' in rest else ('exit' if rest.strip()=='exit' else 'X')
            if ' call ' in ' '+rest and ';' not in rest: lb='X'
            c[lb]+=1
            if lb==lab and c[lb]==occ: print('==',p); print('\n'.join(cur)); break
            cur=[]
