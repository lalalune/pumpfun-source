#!/usr/bin/env python3
"""llfn.py <m.ll> <out.bin> [llc args]: llc the slim module, write execute's bytes."""
import sys,os,subprocess,tempfile
T=os.path.dirname(os.path.abspath(__file__))
m,ob=sys.argv[1],sys.argv[2]
o=tempfile.mktemp(suffix='.o',dir=os.path.dirname(os.path.abspath(m)))
subprocess.run([os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llc'),'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',m,'-filetype=obj','-o',o,*sys.argv[3:]],check=True)
g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
open(ob,'wb').write(g['elf_fn'](o,g['KEEP'])); os.remove(o)
