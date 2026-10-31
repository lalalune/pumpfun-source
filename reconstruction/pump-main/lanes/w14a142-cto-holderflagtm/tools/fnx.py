#!/usr/bin/env python3
# fnx.py <x.o> <out.bin>: extract admin_cto fn bytes
import sys,os
T=os.path.dirname(os.path.abspath(__file__)); g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
open(sys.argv[2],'wb').write(g['elf_fn'](sys.argv[1],g['KEEP']))
