#!/usr/bin/env python3
"""objfn.py x.o out.bin : extract admin_cto execute bytes from an llc object."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
open(sys.argv[2],'wb').write(G['elf_fn'](sys.argv[1],G['KEEP']))
