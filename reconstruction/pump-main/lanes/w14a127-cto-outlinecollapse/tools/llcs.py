#!/usr/bin/env python3
"""llcs.py <name> <post-opt slim m.ll> [llc args]: llc only (no opt) + score; writes rx/<name>/fn.bin, res.json"""
import sys,os,subprocess,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
n,m=sys.argv[1:3]; d=f'{OUT}/rx/{n}'; os.makedirs(d,exist_ok=True)
if os.path.abspath(m)!=d+'/m.ll': subprocess.run(['cp',m,d+'/m.ll'],check=True)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o',*sys.argv[3:]],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(cand)
rr,sd=oracle.metric(cand,oracle.orig_window()); print(json.dumps({'name':n,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd}))
