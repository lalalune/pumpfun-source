#!/usr/bin/env python3
"""dis.py <unstripped.so> [out.txt]: dump admin_cto::execute as 'rel_off  text' lines (offset relative to function start)."""
import sys,re
from pathlib import Path
H=Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a03-shim-unlockspill/reconstruction/harness')
sys.path.insert(0,str(H))
from win import Cand, objdump_text, demangle, find_window, resolve_original, BASE
so=sys.argv[1]
if so=='orig':
    st,w=find_window('0x22a10'); d=objdump_text(resolve_original(BASE/'original.so'),st,st+w['bytes'])
else:
    c=Cand(so)
    s,n=[(s,n) for s,n,nm in c.funcs if re.search(r'admin_cto::execute$',demangle(nm))][0]
    d=c.disassembly(s,n); st=s
out=open(sys.argv[2],'w') if len(sys.argv)>2 else sys.stdout
for a,t in d.items(): out.write(f"{a-st:#06x}  {t}\n")
