#!/usr/bin/env python3
"""rxt.py <name> <in.ll> [--jt N] [--keep]: run the post-JT2 tail pipeline (dbg opt) on a module dumped before execute's 2nd JT, llc, score."""
import sys,os,subprocess,json,time
sys.path.insert(0,os.path.dirname(__file__)); import oracle
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a27-cto-jtbb75hop')
DBG=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/opt')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
a=sys.argv[1:]; name=a.pop(0); inp=a.pop(0); extra=os.environ.get('OPTX','').split()
d=OUT+'/rx/'+name; os.makedirs(d,exist_ok=True); t0=time.time()
pipe=open(OUT+'/'+os.environ.get('PIPE','tailpipe.txt')).read().strip()
if 'jt-force' in pipe: extra=['-load-pass-plugin',OUT+'/plug/jtf.dylib']+extra
r=subprocess.run([DBG,'-passes='+pipe,*extra,inp,'-S','-o',d+'/o3.ll'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
if r.stderr: open(d+'/opt.err','w').write(r.stderr)
o=open(d+'/o3.ll').read(); open(d+'/m.ll','w').write(oracle.slim(o)); os.remove(d+'/o3.ll')
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
cand=oracle.elf_fn(d+'/m.o',oracle.KEEP); open(d+'/fn.bin','wb').write(cand)
orig=oracle.orig_window(); rr,sd=oracle.metric(cand,orig)
res={'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd,'secs':round(time.time()-t0,1)}
bs=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
res['eq_main']=oracle.mask(oracle.elf_fn(bs,oracle.KEEP))==oracle.mask(cand)
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
