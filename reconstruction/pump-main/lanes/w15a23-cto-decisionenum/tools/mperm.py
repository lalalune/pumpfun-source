#!/usr/bin/env python3
"""mperm.py <unstripped.so>...: M, Mperm (binary spill-set approximation via binspills) per candidate."""
import sys,os,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import relab as R
for so in sys.argv[1:]:
    b=R.g['elf_fn'](so,R.g['KEEP']); sp=R.binspills(b)
    m0=R.M(b); mb,pm=R.bestperm(b,sp,4)
    print(json.dumps({'so':so.split('/')[-2],'bytes':len(b),'M':m0,'nsp':len(sp),'Mperm':mb,'ratio_perm':R.ratio(R.apply(b,pm))}),flush=True)
