#!/usr/bin/env python3
"""dis.py <unstripped.so> [symregex] : disassemble admin_cto::execute of a candidate (addr  text)."""
import sys,re
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[4]/'harness'))
p=sys.argv[1]; rx=sys.argv[2] if len(sys.argv)>2 else r'admin_cto7execute17'
sys.argv=['x']
import score, win
from pathlib import Path
f=next(x for x in score.candidate_functions(Path(p)) if re.search(rx,x[2]))
for ad,t in win.objdump_text(Path(p),f[0],f[0]+f[1]).items(): print(f"{ad:#07x}  {t}")
