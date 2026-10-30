#!/usr/bin/env python3
"""regcmp.py a.dis b.dis [mode fm|sk|raw] [seg]: per-orig-chunk matched instruction counts for two candidates."""
import sys,difflib,collections
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a52-cto-ovarm/tools')
from absratio import norm,O
mode=sys.argv[3] if len(sys.argv)>3 else 'fm'; seg=int(sys.argv[4],16) if len(sys.argv)>4 else 0x400
def n(x): return x.strip() if mode=='raw' else norm(x,mode=='sk')
OL=[l.split(None,1) for l in open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a52-cto-ovarm/orig.rel') if len(l.split(None,1))>1]
oa=[int(x[0],16) for x in OL]; on=[n(x) for x in O]
res=[]
for f in sys.argv[1:3]:
    C=[l.split(None,1)[1] for l in open(f) if len(l.split(None,1))>1]
    cnt=collections.Counter()
    for b in difflib.SequenceMatcher(None,on,[n(x) for x in C],autojunk=False).get_matching_blocks():
        for k in range(b.size): cnt[oa[b.a+k]//seg]+=1
    res.append(cnt)
tot=collections.Counter(a//seg for a in oa)
for k in sorted(tot):
    d=res[1][k]-res[0][k]
    print('%05x %4d %4d %4d %+4d'%(k*seg,tot[k],res[0][k],res[1][k],d), '*' if abs(d)>=5 else '')
print('sum',sum(res[0].values()),sum(res[1].values()))
