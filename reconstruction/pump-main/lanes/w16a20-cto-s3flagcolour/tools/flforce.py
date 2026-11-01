#!/usr/bin/env python3
"""flforce.py <m.ll> <force> [w ...]: S3-type build under RAPRIO_FORCE (sticky) with the holder-flag spill weight set
by the SSC hook (experiment only). Prints M natural and for each weight w (flag:=w), with the flag offset."""
import sys,os,json,re,subprocess
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import flagcol as F
OUT=os.path.dirname(T); LLC=OUT+'/llvmb/bin/llc'
ll=sys.argv[1]; force=sys.argv[2]; ws=sys.argv[3:] or ['0.0005']
os.environ['RAPRIO_STICKY']='1'
if force and force!='-': os.environ['RAPRIO_FORCE']=force
else: os.environ.pop('RAPRIO_FORCE',None)
tmp=OUT+'/an/flforce.%d.mir'%os.getpid()
subprocess.run([LLC,*F.A,ll,'-stop-before=stack-slot-coloring','-o',tmp],capture_output=True)
mir=open(tmp).read().split('\n'); os.remove(tmp); flag=None
for i,l in enumerate(mir):
    m=re.match(r'\s+STB_V1 killed \$(r\d), killed \$(r\d), 165\b',l)
    if m:
        for j in range(i-1,max(i-6,0),-1):
            mm=re.match(r'\s+\$%s = LDD_V1 %%stack\.(\d+), 0\s*$'%m.group(1),mir[j])
            if mm: flag=int(mm.group(1)); break
        break
out={'force':force[:60],'flag':flag}
for s in ['-']+[f'{flag}:={w}' for w in ws if flag]:
    r=F.run(ll,s,[flag] if flag else [])
    r=r[0] if isinstance(r,tuple) else r
    out[s]=(r['M'],r['bytes'],(r.get(f'SS{flag}') or {}).get('off') if flag else None)
print(json.dumps(out))
