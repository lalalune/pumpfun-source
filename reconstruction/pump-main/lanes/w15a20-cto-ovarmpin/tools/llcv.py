#!/usr/bin/env python3
"""llcv.py <name> <tag> [llc args...]: re-run llc on rx/<name>/m.ll with extra args; report ratio, bytes, sharing-CPI call position."""
import sys,os,subprocess,json,struct
sys.path.insert(0,os.path.dirname(__file__)); import oracle
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
name,tag=sys.argv[1],sys.argv[2]; extra=sys.argv[3:]
src=sys.argv[1] if sys.argv[1].endswith('.ll') else f'{OUT}/rx/{name}/m.ll'
d=f'{OUT}/rx/{os.path.basename(name).replace(".ll","")}__{tag}'; os.makedirs(d,exist_ok=True)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',src,'-filetype=obj','-o',d+'/m.o',*extra],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
c=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(c)
rr,sd=oracle.metric(c,oracle.orig_window())
# find position of the call to admin_cto_sharing_config via relocation: approximate = largest gap? use objdump symbolized relocs
o=subprocess.run([SDK+'/llvm-objdump','-dr','--no-show-raw-insn',d+'/m.o'],capture_output=True,text=True).stdout
pos=None;base=None
for l in o.split('\n'):
    if 'admin_cto7execute' in l and l.endswith('>:'): base=0
    if base is not None and 'admin_cto_sharing_config' in l:
        try: pos=int(l.split(':')[0].strip(),16)
        except: pass
        break
res={'name':os.path.basename(d),'ratio':round(rr,5),'bytes':len(c),'slots_diff':sd,'share_call':hex(pos) if pos is not None else None}
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
