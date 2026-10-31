#!/usr/bin/env python3
"""tailfi.py <pre.mir> <ssc.log>: for the sharing-CPI tail reloads (LDD %stack.N -> ST* into _55.i98 array), print
pre-colour FI, its weight, colour (from -debug-only=stack-slot-coloring log), final offset (0x8e0+8*(c-179)),
the spill-store positions (MIR line) of FI N, and the array offset."""
import re,sys
mir=open(sys.argv[1]).read().split('\n'); log=open(sys.argv[2]).read()
W={int(a):float(b) for a,b in re.findall(r'^SS#(\d+) .* weight:(\S+)$',log,re.M)}
COL={int(a):int(b) for a,b in re.findall(r'Assigning fi#(\d+) to fi#(\d+)',log)}
st={}
for i,l in enumerate(mir):
    m=re.search(r'STD_V1 (?:killed )?\$r\d+, %stack\.(\d+), 0\s*(?:$|::)',l)
    if m: st.setdefault(int(m.group(1)),[]).append(i)
rows=[]
for i,l in enumerate(mir):
    m=re.match(r'\s+\$(r\d+) = LDD_V1 %stack\.(\d+), 0\s*$',l)
    if not m: continue
    n=mir[i+1]; m2=re.match(r'\s+(ST\w+) killed \$'+m.group(1)+r', %stack\.\d+\._55\.i9\d, (\d+)',n)
    if m2:
        fi=int(m.group(2)); c=COL.get(fi,fi)
        rows.append((i,fi,W.get(fi),c,0x8e0+8*(c-179),int(m2.group(2)),m2.group(1),st.get(fi,[])))
for r in rows: print(r[0],'fi',r[1],'w %.4g'%r[2] if r[2] else None,'col',r[3],hex(r[4]),'arr',r[5],r[6],'st@',r[7])
