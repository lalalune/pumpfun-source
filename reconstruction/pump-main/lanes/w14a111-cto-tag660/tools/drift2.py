#!/usr/bin/env python3
"""drift2.py <m.o>: matching-block drift (cand byte offset - orig byte offset) along execute, in 0x400 bins."""
import sys,os,difflib
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
A=sys.argv[1:]; sys.argv=['x','n']
exec(open(D+'tools/rx.py').read().split('OUT=os.environ')[0])
o=mask(orig_window()); c=mask(elf_fn(A[0],KEEP))
def offs(t):
    r=[];x=0
    for k in t: r.append(x); x+=len(k)
    return r
oo=offs(o); co=offs(c)
sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
bins={}
for b in sm.get_matching_blocks():
    for i in range(b.size):
        a=oo[b.a+i]; d=co[b.b+i]-a
        bins.setdefault(a//0x800,{}).setdefault(d,0); bins[a//0x800][d]+=1
for k in sorted(bins):
    top=sorted(bins[k].items(),key=lambda x:-x[1])[:3]
    print(hex(k*0x800), ' '.join('%+d:%d'%(d//8,n) for d,n in top))
