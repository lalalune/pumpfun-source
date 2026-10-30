#!/usr/bin/env python3
"""px.py <name> [edits.py] [--base post.ll] [--opt PASSES]: post-opt IR oracle (experiment only).
Slims the real build's post-opt module (cappost.py) to admin_cto::execute, applies EDITS (exact (old,new) pairs or
callables), optionally runs `opt -passes=PASSES`, then llc exactly like fastbuild; prints ratio/slots/M/bytes/eq_main."""
import sys,os,subprocess,runpy,json,difflib,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import rx_lib as R
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a32-cto-stcreatorrb')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
OPT=R.OPT
a=sys.argv[1:]; name=a.pop(0); edits=None; base=OUT+'/ir/mainp.m.ll'; passes=None
while a:
    x=a.pop(0)
    if x=='--base': base=a.pop(0)
    elif x=='--opt': passes=a.pop(0)
    else: edits=x
d=OUT+'/px/'+name; os.makedirs(d,exist_ok=True); t0=time.time()
t=open(base).read()
if not base.endswith('.m.ll'): t=R.slim(t)
if edits:
    g=runpy.run_path(edits)
    for e in g['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/m.ll','w').write(t)
if passes:
    r=subprocess.run([OPT,'-passes='+passes,d+'/m.ll','-S','-o',d+'/m.ll'],capture_output=True,text=True)
    if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o']+os.environ.get('LLCARGS','').split(),capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
cand=R.elf_fn(d+'/m.o',R.KEEP)
O=R.mask(R.orig_window()); C=R.mask(cand)
sm=difflib.SequenceMatcher(None,O,C,autojunk=False)
ob=b''.join(O); cb=b''.join(C)
sd=sum(1 for i in range(0,len(ob),8) if ob[i:i+8]!=cb[i:i+8]) if len(ob)==len(cb) else None
res={'name':name,'ratio':round(sm.ratio(),5),'bytes':len(cand),'slots_diff':sd,'M':sum(x[2] for x in sm.get_matching_blocks()),'secs':round(time.time()-t0,1)}
bs=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
res['eq_main']=R.mask(R.elf_fn(bs,R.KEEP))==C
print(json.dumps(res)); open(d+'/res.json','w').write(json.dumps(res))
