"""Residual windows under full original order with fixed sizes (lists the call that breaks each). Usage: resid.py <unstripped.so> <refined.json>"""
import sys,json,re
sys.path.insert(0,__file__.rsplit('/',1)[0])
from m13 import *
M=model(sys.argv[1],sys.argv[2])
fix=lambda a: M.wins[M.inv[a]]['bytes'] if a in M.inv and M.inv[a] in M.UN else M.units[a][0]
o=sorted([a for a in M.cst if a in M.inv],key=lambda a:M.inv[a])
r=M.eval(o,fix)
na={};p=M.text0
for a in o: na[a]=p; p+=fix(a)
nm=lambda a: re.sub(r'17h[0-9a-f]{16}E$','',M.names[a])[:90]
print('full order fixed sizes',len(r),'text',hex(p-M.text0),hex(M.osec['.text']['size']))
for st,a,calls,tl,hd in M.checks:
    if st in r: continue
    bad=[(hex(M.inv.get(c,0)),nm(c),(na[c]+coff-(na[a]+off+8)-od) if c in na else 'extra-unit') for off,c,coff,od in calls if c not in na or na[c]+coff-(na[a]+off+8)!=od]
    badt=[(hex(c),oabs) for c,coff,oabs in tl if c not in na or na[c]+coff!=oabs]
    print(hex(st),nm(a),bad[:4],badt[:3])
