#!/usr/bin/env python3
"""fdelta.py <m.dis>: align with orig (frame-masked) and histogram (orig_off -> cand_off) frame-offset pairs."""
import sys,re,difflib,collections
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a31-cto-lv3relayout/tools')
from absratio import norm,O
C=[l.split(None,1)[1] for l in open(sys.argv[1]) if len(l.split(None,1))>1]
a=[norm(x,False) for x in O]; b=[norm(x,False) for x in C]
def off(s):
    m=re.search(r'r10 - 0x([0-9a-f]+)',s) or re.search(r'add64 r\d, -0x([0-9a-f]+)$',s.strip())
    return int(m.group(1),16) if m else None
pairs=collections.Counter()
for bl in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
    for k in range(bl.size):
        o=off(O[bl.a+k]); c=off(C[bl.b+k])
        if o is not None and c is not None: pairs[(o,c)]+=1
byo=collections.defaultdict(collections.Counter)
for (o,c),n in pairs.items(): byo[o][c]+=n
tot=sum(pairs.values()); same=sum(n for (o,c),n in pairs.items() if o==c)
print(f'frame refs aligned {tot}, exact {same}')
# delta summary per orig range
rows=[]
for o in sorted(byo):
    c,n=byo[o].most_common(1)[0]; rows.append((o,c,n,sum(byo[o].values())))
cur=None
for o,c,n,t in rows:
    d=c-o
    if cur and cur[2]==d: cur[1]=o; cur[3]+=t
    else:
        if cur: print(f'  orig {cur[0]:#06x}-{cur[1]:#06x} delta {cur[2]:+#x} refs {cur[3]}')
        cur=[o,o,d,t]
print(f'  orig {cur[0]:#06x}-{cur[1]:#06x} delta {cur[2]:+#x} refs {cur[3]}')
