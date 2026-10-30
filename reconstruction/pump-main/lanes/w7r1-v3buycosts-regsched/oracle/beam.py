#!/usr/bin/env python3
"""beam.py classes width depth : beam search over IR mutations, minimizing '-' diff lines vs original."""
import sys,os,json
sys.path.insert(0,os.path.dirname(__file__))
import mut
from concurrent.futures import ThreadPoolExecutor
classes=sys.argv[1].split(','); W=int(sys.argv[2]); D=int(sys.argv[3])
f0=mut.F0
if os.environ.get('EDIT'):
    import runpy
    for e in os.environ['EDIT'].split(':'): f0=runpy.run_path(e)['edit'](f0)
b=mut.run(('base',f0)); print('BASE',b,flush=True)
beam=[(b[0],b[1],b[2],[],f0)]
if os.environ.get('SEEDS'):
    import json
    beam=[]
    for sd in os.environ['SEEDS'].split('|'):
        g=[j for j in mut.allmuts(f0,classes) if j[0]==sd][0]; r=mut.run(g); beam.append((r[0],r[1],r[2],[sd],g[1])); print('SEED',r)
seen=set([hash(f0)])
ex=ThreadPoolExecutor(int(os.environ.get('J','6')))
log=open(mut.OUT+'/beam-%s.log'%os.environ.get('NAME','x'),'w')
for d in range(D):
    jobs=[]
    for sc,sz,sig,tags,f in beam:
        for tag,g in mut.allmuts(f,classes):
            h=hash(g)
            if h in seen: continue
            seen.add(h); jobs.append((tags+[tag],g))
    res=list(ex.map(lambda j:(mut.run((j[0][-1],j[1])),j),jobs))
    res=[(r[0],r[1],r[2],j[0],j[1]) for r,j in res if r[2]!='ERR']
    PEN=lambda x:x[0]+(0 if x[2][1:2]=='2' or not os.environ.get('SRET') else 1000)
    res.sort(key=lambda x:(PEN(x),len(x[3])))
    print('depth',d,'jobs',len(jobs),'best',[(x[0],x[1],x[2],x[3]) for x in res[:3]],flush=True)
    for x in res[:50]: log.write(json.dumps([x[0],x[1],x[2],x[3]])+'\n')
    log.flush()
    if res and res[0][0]==0:
        open(mut.OUT+'/irexp/beam-hit.ll','w').write(res[0][4]); print('HIT',res[0][3]); break
    beam=res[:W]
