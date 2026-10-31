#!/usr/bin/env python3
"""post.py <results.jsonl> <out.jsonl>: for each captured build: base, +h7, +B (validate relay), +h7+B; sc scores + chunks vs main."""
import sys,os,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); O=os.path.dirname(T); sys.path.insert(0,T)
import sc, relayn, fbound
R=sc.score(O+'/rx/m/m.o')
done=set()
if os.path.exists(sys.argv[2]):
    for l in open(sys.argv[2]): done.add(json.loads(l)['name'])
def rec(n,v,path,extra={}):
    s=sc.score(path); ch=s.pop('ch'); s.update(extra)
    s['dch']={f'{k:#06x}':[a[0]-R['ch'][k][0],a[1]-R['ch'][k][1]] for k,a in sorted(ch.items())}
    s.update({k:v2 for k,v2 in fbound.bound(path).items() if k in ('fR','rfR','rfjR')})
    s['name']=n; s['v']=v; return s
for l in open(sys.argv[1]):
    r=json.loads(l); n=r['name']
    if 'ratio' not in r or n in done: continue
    d=f'{O}/rx/{n}'; out=[]
    if not os.path.exists(d+'/m.s'): subprocess.run(['bash',T+'/llc.sh',d+'/m.ll',d+'/m.s'],check=True)
    out.append(rec(n,'base',d+'/m.s'))
    h=subprocess.run(['python3',T+'/h7.py',d+'/m.ll',d+'/h7.ll'],capture_output=True,text=True)
    vs=[('base',d+'/m.s')]
    if h.returncode==0:
        subprocess.run(['bash',T+'/llc.sh',d+'/h7.ll',d+'/h7.s'],check=True); os.remove(d+'/h7.ll')
        out.append(rec(n,'h7',d+'/h7.s')); vs.append(('h7',d+'/h7.s'))
    for v,p in vs:
        try:
            x=relayn.run(p,p[:-2]+'B.s','B')
            out.append(rec(n,v+'+B',p[:-2]+'B.s',{'miss':x['miss']}))
        except Exception as e: out.append({'name':n,'v':v+'+B','err':repr(e)[:200]})
    with open(sys.argv[2],'a') as f:
        for x in out: f.write(json.dumps(x)+'\n')
    for x in out: print(n,x.get('v'),{k:x.get(k) for k in ('ratio','bytes','M','jM','fR','rfR','rfjR','skM','miss','err')})
