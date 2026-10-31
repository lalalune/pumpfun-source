import json,sys
M=[116,94,109,195,198,195,174,199,130,213,214,208,205,86]; ML=[0.66986,0.69982,0.784]
R=[]
for f in sys.argv[1:]:
    R+=[json.loads(l) for l in open(f)]
R=[r for r in R if 'L' in r and r.get('kind')!='ctl']
for r in R: r['d']=sum(r['ch'][5:8])-sum(M[5:8]); r['dL2']=round(r['L'][2]-ML[2],5); r['dL1']=round(r['L'][1]-ML[1],5)
print('L2-neutral (dL2>=-0.0005) with clone-run gain:')
for r in sorted(R,key=lambda r:-r['d']):
    if r['d']>0 and r['dL2']>=-0.0005: print(' ',r['name'],r['bytes'],r['L'],r['d'],r['dL2'])
print('top by clone-run delta:')
for r in sorted(R,key=lambda r:-r['d'])[:8]: print(' ',r['name'],r['bytes'],r['L'],r['d'],r['dL2'],r['ch'][5:8])
print('top by L1:')
for r in sorted(R,key=lambda r:-r['L'][1])[:5]: print(' ',r['name'],r['bytes'],r['L'],r['d'],r['dL2'])
print(len(R),'variants')
