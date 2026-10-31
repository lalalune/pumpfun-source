#!/usr/bin/env python3
"""bpsplit.py <bp.txt>: split debug MBP log into passes; write dec1/ord1/dec2/ord2 next to it, with long names shortened."""
import sys,re,os
p=sys.argv[1]; d=os.path.dirname(p); L=open(p).read().split('\n')
def sh(s):
    s=re.sub(r"_ZN(?:\d+[^']*?)?(\d+)(to_string|clone|inc_strong|drop_in_place)[^']*?E(\.[\w.]*)?'",lambda m:f"{m[2]}{m[3] or ''}'",s)
    s=re.sub(r"_ZN[^']{40,}?17h[0-9a-f]{16}E(\.[\w.]*)?'",lambda m:f"FN{m[1] or ''}'",s)
    return s
parts=[[]]
for l in L:
    if l.startswith('[MBP] Function'): parts.append([]); continue
    parts[-1].append(sh(l))
# parts[0]=dec1, parts[1]=ord1+dec2, parts[2]=ord2
def splitord(x):
    o=[];i=0
    while i<len(x) and (x[i].startswith('Placing chain') or x[i].startswith('          ...')): o.append(x[i]); i+=1
    return o,x[i:]
o1,d2=splitord(parts[1]); o2,_=splitord(parts[2])
for nm,x in (('dec1',parts[0]),('ord1',o1),('dec2',d2),('ord2',o2)): open(f'{d}/{nm}.txt','w').write('\n'.join(x)+'\n')
print({k:len(v) for k,v in (('dec1',parts[0]),('ord1',o1),('dec2',d2),('ord2',o2))})
