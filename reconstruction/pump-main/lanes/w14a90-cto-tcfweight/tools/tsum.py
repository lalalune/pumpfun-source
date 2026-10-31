import json,sys
B=json.loads(sys.argv[1]); M=B['ch']; ML=B['L']
R=[]
for f in sys.argv[2:]: R+=[json.loads(l) for l in open(f)]
R=[r for r in R if 'L' in r and r.get('kind')!='ctl']
for r in R: r['d']=sum(r['ch'][5:8])-sum(M[5:8]); r['dL2']=round(r['L'][2]-ML[2],5); r['dL1']=round(r['L'][1]-ML[1],5)
for r in sorted(R,key=lambda r:-r['dL1'])[:10]: print(' ',r['name'],r['bytes'],r['L'],'d',r['d'],'dL1',r['dL1'],'dL2',r['dL2'],r['ch'][4:8])
print(len(R))
