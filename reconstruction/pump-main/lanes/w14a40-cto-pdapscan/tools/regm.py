#!/usr/bin/env python3
"""regm.py <fn.bin|m.o>...: per 0x800 region exact counts with registers masked (R) and with regs+stack offsets masked (RF)."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
def m2(toks,fr):
    out=[]
    for t in toks:
        b=bytearray(t); b[1]=0
        if fr and len(b)==8 and ((b[0]&7) in (1,2,3)): b[2:4]=b'\0\0'  # ld/st offsets
        out.append(bytes(b))
    return out
o0=g['mask'](g['orig_window']()); W=0x800//8
for fr in (0,1):
    o=m2(o0,fr)
    for p in sys.argv[1:]:
        c=m2(g['mask'](open(p,'rb').read() if p.endswith('.bin') else g['elf_fn'](p,g['KEEP'])),fr)
        sm=difflib.SequenceMatcher(None,o,c,autojunk=False); cnt=[0]*(len(o)//W+1)
        for a,b,k in sm.get_matching_blocks():
            for j in range(k): cnt[(a+j)//W]+=1
        print('RF' if fr else 'R ','%-12s %.5f '%(p.split('/')[-2],sm.ratio())+' '.join('%4d'%x for x in cnt),'sum',sum(cnt))
