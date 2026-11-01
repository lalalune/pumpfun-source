#!/usr/bin/env python3
"""frc.py <m.ll> <name> [FORCE] : patched llc (w15a24 RAPRIO) with RAPRIO_FORCE, then M + region dM vs main. Experiment only."""
import sys,os,subprocess,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,regprof,numpy as np
from regs import R
LLC=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a04-cto-lanchorceil/llvmb/bin/llc')
A=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a14-cto-vcretune/frc')
m,name=sys.argv[1],sys.argv[2]; F=sys.argv[3] if len(sys.argv)>3 else ''
os.makedirs(OUT+'/'+name,exist_ok=True); d=OUT+'/'+name
env=dict(os.environ); env['RAPRIO_STICKY']='1'
if F: env['RAPRIO_FORCE']=F
subprocess.run([LLC,*A,m,'-filetype=obj','-o',d+'/f.o'],env=env,check=True)
c=oracle.elf_fn(d+'/f.o',oracle.KEEP); open(d+'/fn.bin','wb').write(c); os.remove(d+'/f.o')
HR=regprof.hits('main')[0]; h,_=regprof.hits(d+'/fn.bin'); OO=np.array(regprof.OO); dr={}
for lo,hi,n in R:
    mm=(OO>=lo)&(OO<hi); x=int(h[mm].sum()-HR[mm].sum())
    if x: dr[n]=x
print(json.dumps({'name':name,'bytes':len(c),'M':int(h.sum()),'dM':int(h.sum()-HR.sum()),'force':F,'dreg':dr}))
