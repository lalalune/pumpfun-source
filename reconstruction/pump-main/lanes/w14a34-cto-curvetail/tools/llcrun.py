#!/usr/bin/env python3
"""llcrun.py <name> <m.ll> <edits.py>: apply post-opt IR EDITS (callables or (old,new)) and run llc like rx.py; print ratio. Experiment only."""
import sys,os,subprocess,runpy,json
T=os.path.dirname(os.path.abspath(__file__)); src=open(T+'/rx.py').read().split('OUT=os.environ')[0]; exec(src)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
n,ml,ep=sys.argv[1:4]; d=os.path.dirname(T)+'/rx/'+n; os.makedirs(d,exist_ok=True)
t=open(ml).read()
for e in runpy.run_path(ep)['EDITS']:
    if callable(e): t=e(t); continue
    x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/m.ll','w').write(t)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=elf_fn(d+'/m.o',KEEP); rr,sd=metric(cand,orig_window())
M=None
o=mask(orig_window()); c=mask(cand)
import difflib
M=sum(b.size for b in difflib.SequenceMatcher(None,o,c,autojunk=False).get_matching_blocks())
print(json.dumps({'name':n,'ratio':round(rr,5),'bytes':len(cand),'slots_diff':sd,'M':M}))
os.remove(d+'/m.ll')
