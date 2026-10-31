import json,sys
R=[json.loads(l) for l in open(sys.argv[1])]
D={(r['v'],r['k'],r['kind']):r for r in R if 'L' in r}
rows=[]
for (v,k,kind),r in D.items():
    if kind=='ctl': continue
    c=D.get((v,k,'ctl'))
    if not c: continue
    dl1=r['L'][1]-c['L'][1]; dl2=r['L'][2]-c['L'][2]; dch=sum(r['ch'][5:8])-sum(c['ch'][5:8])
    rows.append((dch,round(dl1,5),round(dl2,5),v,k,kind,r['bytes'],c['bytes'],r['L'],c['L'][0]))
rows.sort(key=lambda x:(-x[0],-x[1]))
for x in rows[:int(sys.argv[2]) if len(sys.argv)>2 else 20]: print(x)
print(len(rows),'pairs')
