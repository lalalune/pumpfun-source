#!/usr/bin/env python3
import json,sys,collections
f=sys.argv[1]; base=sys.argv[2] if len(sys.argv)>2 else '85d273bcd66a'; M0=int(sys.argv[3]) if len(sys.argv)>3 else 2287
R=[json.loads(l) for l in open(f)]
err=[r for r in R if 'err' in r]; R=[r for r in R if 'M' in r]
ch=[r for r in R if r['sig']!=base]
print(len(R),'changed',len(ch),'err',len(err), collections.Counter(r['id'].split(':')[0] for r in R))
print('top by M (any size):')
for r in sorted(ch,key=lambda r:(-r['M'],abs(r['bytes']-27400)))[:30]: print(' ',r['id'],r['M'],r['M']-M0,r['bytes']-27400,r['sig'])
