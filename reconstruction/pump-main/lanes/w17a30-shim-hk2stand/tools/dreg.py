#!/usr/bin/env python3
"""dreg.py <ref fn.bin> <cand fn.bin>...: difflib (scored metric) matched tokens per region, cand minus ref,
plus the matching-block list differences in a given orig range (--blocks lo hi)."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import rc
O=rc.orig_window(); ot,oo=rc.mask(O)
def per(p):
    C=rc.elf_fn(p); ct,_=rc.mask(C)
    sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False); d={}
    bl=sm.get_matching_blocks()
    for a,b,n in bl:
        for k in range(n):
            r=rc.reg_of(oo[a+k]); d[r]=d.get(r,0)+1
    return d,sum(x.size for x in bl),bl
a=sys.argv[1:]; blk=None
if '--blocks' in a:
    i=a.index('--blocks'); blk=(int(a[i+1],16),int(a[i+2],16)); del a[i:i+3]
d0,M0,b0=per(a[0]); print('ref',a[0],'M',M0); print('   ',' '.join(f'{n}:{d0.get(n,0)}' for _,n in rc.REG))
for p in a[1:]:
    d,M,b=per(p); print(p,'M',M,f'{M-M0:+d}'); print('   ',' '.join(f'{n}:{d.get(n,0)-d0.get(n,0):+d}' for _,n in rc.REG if d.get(n,0)!=d0.get(n,0)))
    if blk:
        f=lambda bl:[(hex(oo[x]),y,n) for x,y,n in bl if n and blk[0]<=oo[x]<blk[1]]
        print(' ref blocks',f(b0)); print(' cand blocks',f(b))
