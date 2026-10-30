#!/usr/bin/env python3
"""irexp.py <ir-dir> <name> [edit.py]: apply edit(fn_text)->fn_text to admin_cto::execute IR, llc, disassemble, region metric."""
import sys,subprocess,re,os,runpy
L=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w10r1-admincto-region1of6')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
base,name=sys.argv[1:3]; edit=sys.argv[3] if len(sys.argv)>3 else None
mod=open(base+'/pump_recovered.ll').read()
sym=re.search(r'_ZN14pump_recovered9admin_cto7execute17h[0-9a-f]+E',mod).group(0)
i=mod.index('@'+sym+'('); i=mod.rindex('\ndefine',0,i)+1; j=mod.index('\n}\n',i)+3
fn=mod[i:j]; fn2=runpy.run_path(edit)['edit'](fn) if edit else fn
if edit: assert fn2!=fn,'edit changed nothing'
d=L+'/irexp/'+name; os.makedirs(d,exist_ok=True)
open(d+'/m.ll','w').write(mod[:i]+fn2+mod[j:])
open(d+'/execute.ll','w').write(fn2)
extra=sys.argv[4:]
r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/m.ll','-filetype=obj','-o',d+'/m.o']+extra,capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
open(d+'/llc.err','w').write(r.stderr)
t=subprocess.check_output([SDK+'/llvm/bin/llvm-readelf','-sW',d+'/m.o'],text=True)
for l in t.splitlines():
    f=l.split()
    if len(f)>=8 and f[7]==sym: a=int(f[1],16); n=int(f[2])
dis=subprocess.check_output([SDK+'/llvm/bin/llvm-objdump','-d','--no-show-raw-insn','-j','.text',f'--start-address={a:#x}',f'--stop-address={a+n:#x}',d+'/m.o'],text=True)
out=[]
for line in dis.splitlines():
    m=re.match(r'^\s*([0-9a-f]+):\s+(.*)$',line)
    if m: out.append(f'0x{int(m.group(1),10)*8-a:04x} '+re.sub(r'\s+<[^>]*>','',m.group(2).strip()))
open(d+'/fn.dis','w').write('\n'.join(out)+'\n')
print(name,'bytes',n)
subprocess.run(['python3',L+'/tools/region.py','x','--dis',d+'/fn.dis'])
