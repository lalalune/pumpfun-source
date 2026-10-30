#!/usr/bin/env python3
"""pe2.py <base m.ll> <name> <edits.py|-> : post-opt IR edit oracle: llc, ratio, chunk rm, coal (experiment only)."""
import sys,os,runpy,subprocess,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
O=os.path.dirname(T)
base,name,ed=sys.argv[1:4]
t=open(base).read()
if ed!='-':
    for e in runpy.run_path(ed)['EDITS']:
        if callable(e): t=e(t); continue
        a,b=e; c=t.count(a); assert c==1,(c,a[:150]); t=t.replace(a,b)
d=O+'/pe/'+name; os.makedirs(d,exist_ok=True); open(d+'/m.ll','w').write(t)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o',*sys.argv[4:]],capture_output=True,text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand=oracle.elf_fn(d+'/m.o',oracle.KEEP)
rr,sd=oracle.metric(cand,oracle.orig_window())
c=json.loads(subprocess.run([sys.executable,T+'/chunk.py',d+'/m.o'],capture_output=True,text=True).stdout)
k=subprocess.run([sys.executable,T+'/coal.py',d],capture_output=True,text=True).stdout.strip().split(': ',1)[-1]
print(json.dumps({'name':name,'ratio':round(rr,5),'bytes':len(cand),'slots':sd,'rm':c['rm'],'rmV':c['rmV'],'rmT':c['rmT'],'coal':k[:120]}))
