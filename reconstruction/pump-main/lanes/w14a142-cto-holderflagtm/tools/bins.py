#!/usr/bin/env python3
# bins.py <a.o> <b.o> [bin=0x400]: per-orig-bin matched tokens (difflib vs orig) for two candidates
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__))
g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
O=g['mask'](g['orig_window']())
def fn(p): return open(p,'rb').read() if p.endswith('.bin') else g['elf_fn'](p,g['KEEP'])
def per(p):
    k=g['mask'](fn(p)); sm=difflib.SequenceMatcher(None,O,k,autojunk=False); m=[0]*len(O)
    for a,b,n in sm.get_matching_blocks():
        for i in range(a,a+n): m[i]=1
    return m
B=int(sys.argv[3],16) if len(sys.argv)>3 else 0x400
ma=per(sys.argv[1]); mb=per(sys.argv[2])
# token index -> byte offset
off=[];o=0
for t in O: off.append(o); o+=len(t)
bins={}
for i,(x,y) in enumerate(zip(ma,mb)): 
    k=off[i]//B; s=bins.setdefault(k,[0,0]); s[0]+=x; s[1]+=y
for k in sorted(bins): 
    a,b=bins[k]; print('%5x %4d %4d %+d'%(k*B,a,b,b-a))
print('tot',sum(ma),sum(mb))
