#!/usr/bin/env python3
"""mx.py name script.py [base_red.ll]: script defines edit(fn_text)->fn_text; prints ratio/diffslots + entry diff."""
import sys,re,subprocess,difflib,os,runpy
from pathlib import Path
OUT=Path(__file__).resolve().parent.parent
B=Path.home()/'.cache/solana/v1.44/platform-tools/llvm/bin'
name,scr=sys.argv[1],sys.argv[2]
base=sys.argv[3] if len(sys.argv)>3 else str(OUT/'ir/base/red.ll')
t=open(base).read()
m=re.search(r'^define[^\n]*create_token_account_v217h[^\n]*\n.*?^\}\n',t,re.M|re.S)
fn=m.group(0); ns=runpy.run_path(scr); f2=ns['edit'](fn)
assert f2!=fn,'no change'
d=OUT/'mx'/name; d.mkdir(parents=True,exist_ok=True)
(d/'m.ll').write_text(t[:m.start()]+f2+t[m.end():])
r=subprocess.run([str(B/'llc'),'-O3','-filetype=obj','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',str(d/'m.ll'),'-o',str(d/'m.o')]+sys.argv[4:],capture_output=True,text=True)
if r.returncode: print('LLC FAIL',r.stderr[-1500:]); sys.exit(1)
a=subprocess.run([str(OUT/'tools/disobj.sh'),str(d/'m.o')],capture_output=True,text=True).stdout.splitlines()
(d/'fn.n').write_text('\n'.join(a)+'\n')
o=(OUT/'llc/orig.n').read_text().splitlines()
sm=difflib.SequenceMatcher(None,o,a,autojunk=False)
nd=sum(max(i2-i1,j2-j1) for t_,i1,i2,j1,j2 in sm.get_opcodes() if t_!='equal')
e=difflib.SequenceMatcher(None,o[:40],a[:40],autojunk=False).ratio()
print(f'{name}: insns={len(a)} orig={len(o)} ratio={sm.ratio():.4f} diffslots={nd} entry40={e:.3f}')
