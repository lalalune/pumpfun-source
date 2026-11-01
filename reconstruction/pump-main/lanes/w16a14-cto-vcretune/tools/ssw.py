#!/usr/bin/env python3
"""ssw.py <trace with -debug-only=stack-slot-coloring>: spill-slot weights from the 'Spill slot intervals:' section and the colour order."""
import sys,re
t=open(sys.argv[1]).read()
i=t.index('Spill slot intervals:'); j=t.index('Color spill slot intervals:',i)
W={int(m.group(1)):float(m.group(2)) for m in re.finditer(r'^SS#(\d+) .*weight:(\S+)$',t[i:j],re.M)}
A=re.findall(r'Assigning fi#(\d+) to fi#(\d+)',t[j:])
print('order:',' '.join(f'{a}->{b}({W.get(int(a),0):.3f})' for a,b in A[:10]))
