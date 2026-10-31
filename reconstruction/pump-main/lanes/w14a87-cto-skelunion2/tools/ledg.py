import json,subprocess,sys
L,pf,rf,sha,mainM=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],int(sys.argv[5])
R=[json.loads(l) for l in open(pf)]
spec={json.loads(l)['name']:json.loads(l)['spec'] for l in open(rf)}; spec['m']='main'
by={}
for r in R:
    if 'M' in r: by.setdefault(r['name'],[]).append(r)
n=0
for name,rows in by.items():
    key=f'0x22a10-w14-{sha}-skelunion2-{spec.get(name,name)}-v1'
    c=subprocess.run(['python3',L,'check','--dedupe-key',key],capture_output=True,text=True)
    if c.returncode!=0: continue
    note='; '.join(f"{r['v']}: {r['ratio']}@{r['bytes']} M {r['M']} jM {r['jM']} fR {r['fR']} rfR {r['rfR']} rfjR {r['rfjR']} skM {r['skM']}" for r in rows)
    note+=f' | main M {mainM}. B = w14a78 orig-like validate block order (relay oracle), h7 = target hoist (post-opt IR)'
    best=max(rows,key=lambda r:r['M'])
    d={'output':'~/.cache/pumpfun-reconstruction/lanes/w14a87-cto-skelunion2/rx/'+name,'target':{'ratio':rows[0]['ratio'],'slots_diff':None,'cand_bytes':rows[0]['bytes']},'notes':note}
    subprocess.run(['python3',L,'record','--lane','w14a87-cto-skelunion2','--approach','skelunion2','--target','0x22a10','--dedupe-key',key,
      '--hypothesis',f'structural-composite oracle on {sha}: {spec.get(name,name)} (raw-IR capture) x {{base,h7,B,h7+B}}',
      '--status','analyzed' if best['M']>mainM else 'rejected','--data',json.dumps(d)],check=True,capture_output=True); n+=1
print('recorded',n)
