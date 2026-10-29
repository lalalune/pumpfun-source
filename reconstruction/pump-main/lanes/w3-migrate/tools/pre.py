#!/usr/bin/env python3
"""pre.py name edit.py [base_pre.ll]: edit pre-opt module (edit(module_text)->text), clang -O3 middle end, reduce, llc, diff vs orig."""
import sys,subprocess,runpy,os
from pathlib import Path
O=Path(__file__).resolve().parent.parent; SDK=Path.home()/'.cache/solana/v1.44/platform-tools/llvm/bin'
name,scr=sys.argv[1],sys.argv[2]; base=sys.argv[3] if len(sys.argv)>3 else str(O/'pre/base.ll')
t=open(base).read(); t2=runpy.run_path(scr)['edit'](t); assert t2!=t,'nochange'
d=O/'pre'/name; d.mkdir(parents=True,exist_ok=True); (d/'in.ll').write_text(t2)
r=subprocess.run([str(SDK/'clang'),'--target=sbf','-O3','-S','-emit-llvm',str(d/'in.ll'),'-o',str(d/'opt.ll')],capture_output=True,text=True)
if r.returncode: print('CLANG FAIL',r.stderr[-2000:]); sys.exit(1)
subprocess.run(['python3',str(O/'tools/reduce.py'),str(d/'opt.ll'),str(d/'red.ll')],check=True)
os.environ['SHOW']=str(d/'fn.n')
r=subprocess.run(['python3',str(O/'tools/llcdiff.py'),str(d/'red.ll')],capture_output=True,text=True); print(name,r.stdout.strip(),r.stderr[-500:])
