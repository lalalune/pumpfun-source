#!/usr/bin/env python3
"""irexp.py <base-ir-dir> <name> <edit.py> : apply edit(fn_text)->fn_text to execute's IR, llc, report ratio + frame"""
import sys,subprocess,re,os,runpy
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w3-adminCTO')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
base,name,edit=sys.argv[1:4]
mod=open(base+'/pump_recovered.ll').read()
sym=re.search(r'_ZN14pump_recovered9admin_cto7execute17h[0-9a-f]+E',mod).group(0)
i=mod.index('define hidden { i64, ptr } @'+sym); j=mod.index('\n}\n',i)+3
fn=mod[i:j]; fn2=runpy.run_path(edit)['edit'](fn)
assert fn2!=fn,'edit changed nothing'
d=O+'/irexp/'+name; os.makedirs(d,exist_ok=True)
EXTRA_MD=runpy.run_path(edit).get('MD','')
open(d+'/m.ll','w').write(mod[:i]+fn2+mod[j:]+EXTRA_MD)
r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/m.ll','-filetype=obj','-o',d+'/m.o','-print-after=prologepilog','-filter-print-funcs='+sym],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
open(d+'/pei.txt','w').write(r.stderr)
# disassemble function from object
t=subprocess.check_output([SDK+'/llvm/bin/llvm-readelf','-sW',d+'/m.o'],text=True)
for l in t.splitlines():
    f=l.split()
    if len(f)>=8 and f[7]==sym: a=int(f[1],16); n=int(f[2]); sec=f[6]
dis=subprocess.check_output([os.path.expanduser('~/.cache/solana/v1.52/platform-tools/llvm/bin/llvm-objdump'),'-d','--no-show-raw-insn','-j','.text',f'--start-address={a:#x}',f'--stop-address={a+n:#x}',d+'/m.o'],text=True)
out=[]
for line in dis.splitlines():
    m=re.match(r'^\s*([0-9a-f]+):\s+(.*)$',line)
    if m: out.append(f'0x{int(m.group(1),16):x}  '+re.sub(r'\s+<[^>]*>','',m.group(2).strip()))
open(d+'/fn.txt','w').write('\n'.join(out)+'\n')
open(d+'/execute.ll','w').write(fn2)
subprocess.run(['python3',O+'/scripts/allocas.py',d+'/execute.ll'],stdout=open(d+'/allocas.txt','w'))
print(name,'bytes',n)
