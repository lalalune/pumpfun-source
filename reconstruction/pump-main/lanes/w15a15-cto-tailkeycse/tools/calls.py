#!/usr/bin/env python3
"""calls.py <dis>: list call sites with resolved callee names (SYMS=/tmp/syms.txt from llvm-readelf -sW of the baseline)."""
import sys,runpy
sys.argv=['webs.py',sys.argv[1],'--min-span','0x1000000']
import os; g=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'webs.py'))
import re
for i,(o,mn,ops) in enumerate(g['L']):
    if mn=='call':
        n=g['callee'](i); n=re.sub(r'17h[0-9a-f]{16}E$','',n); print(hex(o),n[-90:])
