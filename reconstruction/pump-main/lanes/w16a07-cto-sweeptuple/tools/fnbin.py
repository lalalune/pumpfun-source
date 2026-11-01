#!/usr/bin/env python3
"""fnbin.py <so> <out.bin>: extract admin_cto::execute bytes from an unstripped .so (or 'orig' for the original window)."""
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
src,out=sys.argv[1],sys.argv[2]
b=g['orig_window']() if src=='orig' else g['elf_fn'](src,g['KEEP'])
open(out,'wb').write(b); print(len(b))
