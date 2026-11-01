#!/usr/bin/env python3
"""ssord.py <ra.txt>: order of spill-slot creation (Inline spilling -> 'From original %v' -> SS#n) from a -debug-only=regalloc trace."""
import sys,re
t=open(sys.argv[1]).read().split('\n'); out=[]; seen=set()
i=0
while i<len(t):
    m=re.match(r'Inline spilling GPR:%(\d+) .*weight:(\S+)',t[i])
    if m:
        v=m.group(1); w=m.group(2); orig=v; ss=None
        for j in range(i+1,min(i+6,len(t))):
            m2=re.match(r'From original %(\d+)',t[j])
            if m2: orig=m2.group(1)
            m3=re.search(r'SS#(\d+)',t[j])
            if m3: ss=m3.group(1); break
        if ss and ss not in seen: seen.add(ss); out.append((int(ss),orig,v,w))
    i+=1
for k,(ss,o,v,w) in enumerate(out): print(f'{k:3d} SS#{ss:4d} orig %{o:5s} piece %{v:5s} w {w}')
