#!/usr/bin/env python3
"""wv.py <colmap prefix>: wallet partner vregs: accounts piece at bb24.i (first ldxdw [r10-X] there) and the do_coin pieces
(mov64 rX,0/1 + stxdw to the do_coin slot, and the slot reload) -> prints force strings acc / dcp."""
import sys,re
L=[l.rstrip('\n') for l in open(sys.argv[1]+'.s')]
i=[k for k,l in enumerate(L) if l.endswith('# %bb24.i')][0]
acc=re.search(r' d(\d+)=',L[i+1]).group(1)
# do_coin slot: the stxdw right after the 'mov64 r1, 1' that precedes bb24.i
slot=None
for k in range(i-1,i-16,-1):
    m=re.search(r'stxdw \[r10 - (\d+)\], r\d+\s+# rp \S+ u(\d+)=',L[k])
    if m and re.search(r'mov64 r\d+, [01]\b',L[k-1]): slot=m.group(1)
pcs=[]
for k,l in enumerate(L):
    m=re.search(r'stxdw \[r10 - %s\], r\d+\s+# rp \S+ u(\d+)='%slot,l)
    if m and re.search(r'mov64 r\d+, [01]\b',L[k-1]): pcs.append(m.group(1))
    m=re.search(r'ldxdw r\d+, \[r10 - %s\]\s+# rp \S+ d(\d+)='%slot,l)
    if m: pcs.append(m.group(1))
pcs=sorted(set(pcs),key=int)
import collections
r97=[re.search(r' u(\d+)=',l).group(1) for l in L if '# rp 97.1 ' in l][0]
pcs=[p for p in pcs if int(r97)-3<=int(p)<=int(r97)+1]
print('acc',acc+'=r7'); print('slot',slot); print('dcp',','.join(p+'=r8' for p in pcs))
