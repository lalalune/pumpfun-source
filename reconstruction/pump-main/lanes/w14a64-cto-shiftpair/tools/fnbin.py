#!/usr/bin/env python3
"""fnbin.py <so> <out.bin>: write admin_cto::execute bytes of a candidate .so"""
import sys,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'harness'))
from win import Cand, demangle
c=Cand(sys.argv[1]); SYM=re.compile(r'admin_cto.*execute')
p=[(s,n) for s,n,nm in c.funcs if SYM.search(demangle(nm))] or [(s,n) for s,n,nm in c.funcs if SYM.search(nm)]
s,n=p[0]; open(sys.argv[2],'wb').write(c.fn(s,n))
