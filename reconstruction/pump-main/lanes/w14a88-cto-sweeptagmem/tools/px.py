#!/usr/bin/env python3
"""px.py <name> <base m.ll> [edits.py]: post-opt llc oracle (experiment only). EDITS: (old,new) or callables."""
import sys,os,subprocess,runpy,json,difflib
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
A=sys.argv[1:]; sys.argv=['x','n']
exec(open(D+'tools/rx.py').read().split('OUT=os.environ')[0])
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
name,base=A[0],A[1]; ed=A[2] if len(A)>2 else None
d=D+'px/'+name; os.makedirs(d,exist_ok=True)
t=open(base).read()
if ed:
    g=runpy.run_path(ed)
    for e in g['EDITS']:
        if callable(e): t=e(t); continue
        x,y=e; c=t.count(x); assert c==1,(c,x[:200]); t=t.replace(x,y)
open(d+'/m.ll','w').write(t)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(json.dumps({'name':name,'error':r.stderr[-1500:]})); sys.exit(1)
cand=elf_fn(d+'/m.o',KEEP); open(d+'/fn.bin','wb').write(cand)
o=mask(orig_window()); c=mask(cand)
sm=difflib.SequenceMatcher(None,o,c,autojunk=False); M=sum(b.size for b in sm.get_matching_blocks())
ob=b''.join(o); cb=b''.join(c)
sd=sum(1 for i in range(0,len(ob),8) if ob[i:i+8]!=cb[i:i+8]) if len(ob)==len(cb) else None
bs=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
res={'name':name,'ratio':round(sm.ratio(),5),'M':M,'bytes':len(cand),'slots':sd,'eq_main':mask(elf_fn(bs,KEEP))==c}
print(json.dumps(res))
