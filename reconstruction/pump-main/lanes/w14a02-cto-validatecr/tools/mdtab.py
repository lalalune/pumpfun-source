import json,sys
rf,cf,mainratio=sys.argv[1],sys.argv[2],sys.argv[3]
R={}
for l in open(rf):
    try: d=json.loads(l); R[d['name']]=d
    except: pass
seen=set()
print('| trial | bytes | plain | fm | rm | rm 0x0-0x1800 | rm total | local L rm | chunks rm (0x200 each, 0x0-0x1800) |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |')
for l in open(cf):
    d=json.loads(l)
    if d['name'] in seen: continue
    seen.add(d['name']); r=R.get(d['name'],{})
    rr=r.get('ratio') if d['name']!='main' else float(mainratio)
    print('| %s | %d | %s | %.5f | %.5f | %d | %d | %d | %s |'%(d['name'].replace('_','+'),d['bytes'],rr,d['fm'],d['rm'],d['rmV'],d['rmT'],d['Lrm'],' '.join(str(x) for x in d['rmC'])))
