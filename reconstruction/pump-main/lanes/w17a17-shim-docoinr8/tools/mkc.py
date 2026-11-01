#!/usr/bin/env python3
"""mkc.py <name> <edit ids...>: apply screen edits to ir/m0.s.ll, run fx (keep), print result"""
import json,sys,os
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a17-shim-docoinr8'
sys.path.insert(0,OUT+'/tools'); os.environ['LANE_OUT']=OUT
import fx
from screen import apply
base=os.environ.get('BASE',OUT+'/ir/m0.s.ll'); ef=os.environ.get('EF',OUT+'/scr/ed_m0.jsonl')
L=open(base).read().split('\n')
E={}
for l in open(ef):
    e=json.loads(l); E[e['id']]=e
t=apply(L,[E[i] for i in sys.argv[2:]])
open(OUT+'/ir/'+sys.argv[1]+'.s.ll','w').write(t)
print(json.dumps(fx.run(t,sys.argv[1],keep=True)))
