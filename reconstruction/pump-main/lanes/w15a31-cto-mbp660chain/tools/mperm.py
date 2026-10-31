#!/usr/bin/env python3
"""mperm.py <fn.bin|unstripped.so>...: M and Mperm (w15a08 relab.bestperm on the binary spill-set approximation)."""
import sys,os,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import relab as R
for p in sys.argv[1:]:
    b=open(p,'rb').read() if p.endswith('.bin') else R.g['elf_fn'](p,R.g['KEEP']); sp=R.binspills(b)
    m0=R.M(b); mb,pm=R.bestperm(b,sp,4)
    print(json.dumps({'p':p.split('/')[-2],'bytes':len(b),'M':m0,'nsp':len(sp),'Mperm':mb,'ratio_perm':R.ratio(R.apply(b,pm))}),flush=True)
