#!/usr/bin/env python3
"""mperm.py <name=fn.bin>...: w15a08 relab bestperm (spill-slot relabel bound) on function blobs, spill set from the binary."""
import sys,os,json
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a34-cto-s1clonearray/w08/tools'); import relab as R
for a in sys.argv[1:]:
    n,p=a.split('='); b=open(p,'rb').read(); sp=R.binspills(b)
    m0=R.M(b); mb,pm=R.bestperm(b,sp,3)
    print(json.dumps({'name':n,'bytes':len(b),'M':m0,'Mperm':mb,'spills':len(sp),'moved':sum(1 for k,v in pm.items() if k!=v)}),flush=True)
