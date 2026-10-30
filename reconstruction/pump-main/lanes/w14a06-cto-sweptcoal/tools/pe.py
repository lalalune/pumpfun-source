#!/usr/bin/env python3
"""pe.py <base m.ll> <name> <edits.py>: post-opt IR edit oracle (experiment only). Applies EDITS (exact (old,new) pairs
or callables) to a slim post-opt module, writes pe/<name>/m.ll, runs llcb (ratio/cf) and coal (swept/payload)."""
import sys,os,runpy,subprocess
T=os.path.dirname(os.path.abspath(__file__))
base,name,ed=sys.argv[1:4]
t=open(base).read()
for e in runpy.run_path(ed)['EDITS']:
    if callable(e): t=e(t); continue
    a,b=e; c=t.count(a); assert c==1,(c,a[:150]); t=t.replace(a,b)
d=os.path.join(os.path.dirname(T),'..','..','..','..','..','..','..','.cache') if False else os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a06-cto-sweptcoal/pe/'+name)
os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(t)
r=subprocess.run([sys.executable,T+'/llcb.py',d+'/m.ll'],capture_output=True,text=True); print(name,r.stdout.strip() or r.stderr[-800:])
r=subprocess.run([sys.executable,T+'/coal.py',d+'/m.ll'],capture_output=True,text=True); print(r.stdout.strip().split(': ',1)[-1] or r.stderr[-800:])
