#!/usr/bin/env python3
# irmove.py IN.ll OUT.ll "X>Y" ... : in swap_hop, move block X (with its body) to right after block Y.  "X<Y": before Y.
import sys,re
src,dst=sys.argv[1:3]; moves=sys.argv[3:]
L=open(src).read().split('\n')
s=[i for i,l in enumerate(L) if l.startswith('define') and '8swap_hop17h' in l][0]
e=s
while L[e]!='}': e+=1
body=[re.sub(r'%(\d+)\b',r'%v\1',l) for l in L[s+1:e]]
blocks=[]; cur=['entry',[]]
for l in body:
    m=re.match(r'^([\w.\-]+):',l)
    if m: blocks.append(cur); cur=[m.group(1),[l]]
    else: cur[1].append(l)
blocks.append(cur)
names=[b[0] for b in blocks]
for mv in moves:
    if '>' in mv: x,y=mv.split('>'); after=True
    else: x,y=mv.split('<'); after=False
    xi=[b[0] for b in blocks].index(x); blk=blocks.pop(xi)
    yi=[b[0] for b in blocks].index(y)
    blocks.insert(yi+1 if after else yi, blk)
out=L[:s+1]+[l for b in blocks for l in b[1]]+L[e:]
open(dst,'w').write('\n'.join(out))
