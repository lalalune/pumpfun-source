#!/usr/bin/env python3
"""mvblk.py <src rx name> <out name> <blk>:<after> ...: post-opt IR block move in execute (llc only), score like rx.py."""
import sys,os,re,subprocess,json
sys.path.insert(0,os.path.dirname(__file__)); import oracle
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a13-cto-jointraceback')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src,name,*moves=sys.argv[1:]
nm=f'{OUT}/rx/{src}/m.named.ll'
if not os.path.exists(nm):
    OPT=[p for p in __import__('glob').glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))][0]
    subprocess.run([OPT,'-passes=instnamer',f'{OUT}/rx/{src}/m.ll','-S','-o',nm],check=True)
t=open(nm).read()
m=re.search(r'^define[^\n]*admin_cto7execute[^\n]*\{\n',t,re.M); s=m.end(); e=t.index('\n}\n',s)
body=t[s:e].split('\n')
blocks=[];cur=['__entry',[]]
blocks.append(cur)
for l in body:
    mm=re.match(r'^([A-Za-z0-9_.$"-]+):',l)
    if mm: cur=[mm[1],[]]; blocks.append(cur)
    cur[1].append(l)
for mv in moves:
    b,a=mv.split(':')
    names=[x[0] for x in blocks]; bi=names.index(b); blk=blocks.pop(bi)
    names=[x[0] for x in blocks]; ai=names.index(a); blocks.insert(ai+1,blk)
nb='\n'.join(l for x in blocks for l in x[1])
d=f'{OUT}/rx/{name}'; os.makedirs(d,exist_ok=True)
open(d+'/m.ll','w').write(t[:s]+nb+t[e:])
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(cand)
rr,sd=oracle.metric(cand,oracle.orig_window())
print(json.dumps({'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd}))
os.remove(d+'/m.ll')
