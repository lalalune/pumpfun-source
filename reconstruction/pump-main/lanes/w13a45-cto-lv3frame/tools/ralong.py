#!/usr/bin/env python3
"""ralong.py <regalloc.log> [N]: long-lived vregs (last selectOrSplit interval) with final physreg."""
import sys,re
t=open(sys.argv[1]).read(); N=int(sys.argv[2]) if len(sys.argv)>2 else 20
iv={}
for m in re.finditer(r'^selectOrSplit GPR:%(\d+) (.*?)  weight:(\S+)',t,re.M):
    segs=re.findall(r'\[(\d+)[rBed],(\d+)[rBed]:\d+\)',m.group(2))
    iv[m.group(1)]=(sum(int(b)-int(a) for a,b in segs),int(segs[0][0]) if segs else 0,int(segs[-1][1]) if segs else 0,float(m.group(3)))
k=t.index('REGISTER MAP'); fin=dict(re.findall(r'\[%(\d+) -> \$(r\d+)\]',t[k:]))
L=sorted(((v[0],r,v) for r,v in iv.items() if r in fin),reverse=True)[:N]
for ln,r,v in L: print(f'%{r:5s} {fin[r]:3s} len={ln:6d} span={v[1]}-{v[2]} w={v[3]:.2e}')
