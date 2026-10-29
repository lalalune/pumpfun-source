#!/usr/bin/env python3
"""irexp.py <name> <edit.py>: apply edit(text)->text to base IR, llc it, diff function vs original."""
import sys,subprocess,re,os,runpy
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/exactsol-introspection')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
SYM='_ZN14pump_recovered14pump_recovered16buy_exact_sol_in17h49bc4356a9e68eb0E'
name,edit=sys.argv[1],sys.argv[2]
base=os.environ.get('IRBASE',OUT+'/out/ir-base/pump_recovered.ll')
t=open(base).read()
ns=runpy.run_path(edit); t2=ns['edit'](t)
assert t2!=t, 'edit changed nothing'
d=OUT+'/irexp/'+name; os.makedirs(d,exist_ok=True)
open(d+'/m.ll','w').write(t2)
r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/m.ll','-filetype=obj','-o',d+'/m.o']+sys.argv[3:],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
fn=subprocess.run([OUT+'/scripts/fn.sh',d+'/m.o',SYM],capture_output=True,text=True).stdout
fn=re.sub(r'call -?0x[0-9a-f]+','call X',fn); fn=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',fn)
open(d+'/fn.txt','w').write(fn)
o=open(OUT+'/analysis/orig-norm.txt').read().splitlines(); c=fn.splitlines()
import difflib
diff=[l for l in difflib.unified_diff(o,c,'orig','cand',n=1,lineterm='')]
nd=sum(1 for l in diff if l[:1] in '+-' and l[:3] not in('+++','---'))
print(f'{name}: insns orig={len(o)} cand={len(c)} difflines={nd}')
print('\n'.join(diff[:60]))
