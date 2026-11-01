#!/usr/bin/env python3
"""rx.py <name> [edits.py] [--base raw.ll] [--llc args]: apply EDITS (list of (old,new) exact replacements, each must occur once,
or callables t->t) to the pre-opt module, opt -O3 (SDK rustlib opt), slim to execute, llc like fastbuild, score with oracle.metric."""
import sys,os,subprocess,runpy,json,re,time
sys.path.insert(0,os.path.dirname(__file__))
import oracle
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w17a06-shim-irbeam')
OPT=[p for p in __import__('glob').glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))][0]
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
a=sys.argv[1:]; name=a.pop(0); edits=None; base=OUT+'/ir/base.ll'; llcargs=[]; keep=False
while a:
    x=a.pop(0)
    if x=='--base': base=a.pop(0)
    elif x=='--llc': llcargs=a; a=[]
    elif x=='--keep': keep=True
    else: edits=x
d=OUT+'/rx/'+name; os.makedirs(d,exist_ok=True); t0=time.time()
t=open(base).read()
if edits:
    g=runpy.run_path(edits)
    for e in g['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/in.ll','w').write(t)
r=subprocess.run([OPT,'-O3',d+'/in.ll','-S','-o',d+'/o3.ll'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
o=open(d+'/o3.ll').read()
open(d+'/m.ll','w').write(oracle.slim(o))
if not keep: os.remove(d+'/in.ll'); os.remove(d+'/o3.ll')
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o',*llcargs],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
cand=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(cand)
orig=oracle.orig_window(); rr,sd=oracle.metric(cand,orig)
res={'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd,'secs':round(time.time()-t0,1)}
bs=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
res['eq_main']=oracle.mask(oracle.elf_fn(bs,oracle.KEEP))==oracle.mask(cand)
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
