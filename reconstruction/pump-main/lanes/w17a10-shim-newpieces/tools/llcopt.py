#!/usr/bin/env python3
"""llcopt.py <m.ll> [llc args...]: run SDK llc on a slim post-opt module with extra args, print M/bytes."""
import sys,os,subprocess,json
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/irbeam/tools'); import oracle,fx
LLC=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llc')
m=sys.argv[1]; extra=sys.argv[2:]
o='/tmp/llcopt_%d.o'%os.getpid()
r=subprocess.run([LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',m,'-filetype=obj','-o',o,*extra],capture_output=True,text=True)
if r.returncode: print(r.stderr[-500:]); sys.exit(1)
b=oracle.elf_fn(o,oracle.KEEP); os.remove(o); M,ratio=fx.Mof(b)
print(json.dumps({'m':m.split('/')[-2],'extra':' '.join(extra),'M':M,'bytes':len(b)}))
