#!/usr/bin/env python3
"""llcscore.py <m.ll> <outdir> : llc like rx.py, then score (experiment only)."""
import sys,os,subprocess,json,runpy
here=os.path.dirname(os.path.abspath(__file__))
sys.argv_s=sys.argv
m,d=sys.argv[1],sys.argv[2]; os.makedirs(d,exist_ok=True)
src=open(os.path.join(here,'rx.py')).read().split("OUT=os.environ.get('RX_OUT'")[0]
g={}; exec(src,g)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',m,'-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=g['elf_fn'](d+'/m.o',g['KEEP']); open(d+'/fn.bin','wb').write(cand)
rr,sd=g['metric'](cand,g['orig_window']())
print(json.dumps({'name':os.path.basename(d),'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd}))
