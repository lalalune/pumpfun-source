#!/usr/bin/env python3
import sys,json,collections
f=sys.argv[1]; base=int(sys.argv[2]) if len(sys.argv)>2 else 2248; bb=int(sys.argv[3]) if len(sys.argv)>3 else 27408
R=[json.loads(l) for l in open(f)]
ok=[r for r in R if 'M' in r]; err=[r for r in R if 'err' in r]
print('n',len(R),'ok',len(ok),'err',len(err))
same=[r for r in ok if r['bytes']==bb]
print('same size',len(same),'eq-M',sum(1 for r in same if r['M']==base),'up',sum(1 for r in same if r['M']>base))
k=collections.Counter(r['id'].split(':')[0] for r in ok)
print(k)
print('-- top at base size')
for r in sorted(same,key=lambda r:-r['M'])[:15]: print(r['id'],r['M'],r['M']-base,r['bytes'])
print('-- top any size (M-base, bytes-bb)')
for r in sorted(ok,key=lambda r:-r['M'])[:15]: print(r['id'],r['M'],r['M']-base,r['bytes']-bb)
if err: print('-- errs'); [print(r['id'],r['err'][:200]) for r in err[:5]]
