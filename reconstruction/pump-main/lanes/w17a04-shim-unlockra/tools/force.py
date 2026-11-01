#!/usr/bin/env python3
"""force.py <m.ll> <force-spec> [...]: score the RAPRIO sticky llc with RAPRIO_FORCE=<spec> for each spec. Experiment only."""
import sys,os,json
sys.path.insert(0,os.path.dirname(__file__))
os.environ['VLLC']=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w17a04-shim-unlockra/bin/llc')
os.environ['RAPRIO_STICKY']='1'
import vscreen
vscreen.LLC=os.environ['VLLC']
vscreen.init()
t=open(sys.argv[1]).read()
for spec in sys.argv[2:]:
    if spec=='-': os.environ.pop('RAPRIO_FORCE',None)
    else: os.environ['RAPRIO_FORCE']=spec
    r=vscreen.run((spec,t)); print(json.dumps(r),flush=True)
