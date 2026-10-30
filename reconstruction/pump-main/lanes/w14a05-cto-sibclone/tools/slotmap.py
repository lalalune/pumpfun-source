#!/usr/bin/env python3
"""slotmap.py <orig.dis> <cand.dis>: map orig spill/frame slots to cand slots via register-masked alignment; print per orig slot the cand slot votes."""
import sys,re,difflib,collections
sys.argv+=[]
exec(open(__file__.replace('slotmap.py','side.py')).read().split('o=rd(sys.argv[1])')[0])
o=rd(sys.argv[1]); c=rd(sys.argv[2])
sm=difflib.SequenceMatcher(None,[n2(t) for _,t in o],[n2(t) for _,t in c],autojunk=False)
votes=collections.defaultdict(collections.Counter)
for a,b,n in sm.get_matching_blocks():
    for k in range(n):
        x=re.search(r'r10 - 0x([0-9a-f]+)',o[a+k][1]); y=re.search(r'r10 - 0x([0-9a-f]+)',c[b+k][1])
        if x and y: votes[int(x.group(1),16)][int(y.group(1),16)]+=1
lo=int(sys.argv[3],16) if len(sys.argv)>3 else 0x8c0; hi=int(sys.argv[4],16) if len(sys.argv)>4 else 0xc08
tot=0;ok=0
for s in sorted(votes):
    if lo<=s<hi:
        v=votes[s]; tot+=sum(v.values()); ok+=v.get(s,0)
        print('%x -> %s'%(s,' '.join('%x:%d'%(k,n) for k,n in v.most_common(4))))
print('exact',ok,'of',tot)
