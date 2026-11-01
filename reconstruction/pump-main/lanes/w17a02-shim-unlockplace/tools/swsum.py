import json,sys
R=[json.loads(l) for l in open(sys.argv[1])]
print('runs',len(R))
R=[r for r in R if 'M' in r]
base=int(sys.argv[2]) if len(sys.argv)>2 else 2251
at=[r for r in R if r['bytes']==27400 and r['M']>base]
print('at27400 >',base,':',len(at))
for r in sorted(at,key=lambda r:-r['M'])[:25]: print(r)
off=sorted([r for r in R if r['bytes']!=27400],key=lambda r:-r['M'])[:6]
for r in off: print('off',r)
