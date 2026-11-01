#!/usr/bin/env python3
"""apply1.py <base.ll> <edits.jsonl> <name> <id>[+<id>...]: apply edits and run fx with --keep."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import fx, importlib.util
spec=importlib.util.spec_from_file_location('scr',T+'/pt_screen.py'); scr=importlib.util.module_from_spec(spec); spec.loader.exec_module(scr)
base,ef,name,ids=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4].split('+')
L=open(base).read().split('\n'); E={}
for l in open(ef):
    e=json.loads(l); E[e['id']]=e
t=scr.apply(L,[E[i] for i in ids])
print(json.dumps(fx.run(t,name,keep=True)))
