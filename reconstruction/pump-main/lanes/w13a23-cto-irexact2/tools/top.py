import sys,json,glob
R=[]
for f in sys.argv[2:]:
    R+=[json.loads(l) for l in open(f) if l.strip()]
base=float(sys.argv[1])
R=[r for r in R if 'ratio' in r]
print('n',len(R))
for r in sorted(R,key=lambda r:-r['ratio'])[:45]:
    if r['ratio']!=base: print(r['item'],r['ratio'],r['bytes'],r.get('slots_diff'),r.get('abs_ratio'))
