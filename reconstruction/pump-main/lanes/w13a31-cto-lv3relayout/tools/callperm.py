#!/usr/bin/env python3
"""callperm.py orig.ann cand.ann : align call/exit landmark sequences; print matched runs as (orig range -> cand range)."""
import sys,difflib,re
def lm(p):
    out=[]
    for l in open(p):
        a,rest=l.rstrip('\n').split(None,1)
        if rest.startswith('call'): out.append((int(a,16),'C:'+(rest.split(';')[1].strip() if ';' in rest else 'sys')))
        elif rest.strip()=='exit': out.append((int(a,16),'EXIT'))
    return out
o=lm(sys.argv[1]); c=lm(sys.argv[2])
sm=difflib.SequenceMatcher(None,[x[1] for x in o],[x[1] for x in c],autojunk=False)
bl=[b for b in sm.get_matching_blocks() if b.size]
used=set(); runs=[]
# greedy: repeatedly find longest common substring among unused
import itertools
O=[x[1] for x in o]; C=[x[1] for x in c]; uo=[0]*len(O); uc=[0]*len(C)
while True:
    best=(0,0,0)
    for i in range(len(O)):
        if uo[i]: continue
        for j in range(len(C)):
            if uc[j] or O[i]!=C[j]: continue
            k=0
            while i+k<len(O) and j+k<len(C) and not uo[i+k] and not uc[j+k] and O[i+k]==C[j+k]: k+=1
            if k>best[2]: best=(i,j,k)
    i,j,k=best
    if k<3: break
    for t in range(k): uo[i+t]=1; uc[j+t]=1
    runs.append(best)
runs.sort()
for i,j,k in runs:
    print(f'orig {o[i][0]:05x}-{o[i+k-1][0]:05x}  cand {c[j][0]:05x}-{c[j+k-1][0]:05x}  n={k:3d}  shift={(c[j][0]-o[i][0]):+#x}  {O[i][2:30]} .. {O[i+k-1][2:30]}')
print('unmatched orig',sum(1 for x in uo if not x),'cand',sum(1 for x in uc if not x))
