#!/usr/bin/env python3
"""reg.py <m.o|fn.bin>...: exact masked-token matches per 0x800 orig region (global SequenceMatcher alignment)."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
o=g['mask'](g['orig_window']()); W=0x800//8
for p in sys.argv[1:]:
    c=g['mask'](open(p,'rb').read() if p.endswith('.bin') else g['elf_fn'](p,g['KEEP']))
    sm=difflib.SequenceMatcher(None,o,c,autojunk=False); cnt=[0]*(len(o)//W+1)
    for a,b,k in sm.get_matching_blocks():
        for j in range(k): cnt[(a+j)//W]+=1
    print('%-40s %.5f %5d '%(p.split('/')[-2],sm.ratio(),len(c)*8)+' '.join('%4d'%x for x in cnt),'sum',sum(cnt))
