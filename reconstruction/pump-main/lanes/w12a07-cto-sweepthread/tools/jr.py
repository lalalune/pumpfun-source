#!/usr/bin/env python3
"""jr.py file_r.txt lo hi : print asm range with resolved jump targets and labels for targets."""
import sys,re
p,lo,hi=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
rows=[]
for l in open(p):
    m=re.match(r'0x([0-9a-f]+)\s+(.*)',l.strip())
    if m: rows.append((int(m.group(1),16),m.group(2)))
addrs={a for a,_ in rows}
tg={}
out=[]
for a,t in rows:
    m=re.match(r'(j\w+)(.*?)([+-]0x[0-9a-f]+|[+-]\d+)$',t)
    if m and t.startswith('j'):
        off=int(m.group(3),16) if '0x' in m.group(3) else int(m.group(3))
        dst=a+8+off*8
        tg.setdefault(dst,[]).append(a)
        t=t+'   -> %05x'%dst
    out.append((a,t))
for a,t in out:
    if lo<=a<=hi:
        lab=''
        if a in tg: lab='  <== '+','.join('%05x'%x for x in tg[a][:6])
        print('%05x  %-55s%s'%(a,t,lab))
