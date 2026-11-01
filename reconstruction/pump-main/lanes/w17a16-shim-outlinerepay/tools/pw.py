#!/usr/bin/env python3
"""pw.py <m.ll> <name> "line:a:b;line:a:b": apply llc-time branch weights to a post-opt slim module, llc, write fx/<name>/{m.ll,fn.bin}, print M."""
import sys,os,subprocess,difflib,json,hashlib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
OUT=os.path.dirname(T)
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src,name=sys.argv[1],sys.argv[2]; W=[tuple(map(int,x.split(':'))) for x in (sys.argv[3] if len(sys.argv)>3 else '').split(';') if x]
L=open(src).read().split('\n'); extra=[]
for k,(i,a,b) in enumerate(W):
    assert L[i].lstrip().startswith('br i1'),L[i]
    L[i]=L[i]+', !prof !9998%d'%k; extra.append('!9998%d = !{!"branch_weights", i32 %d, i32 %d}'%(k,a,b))
d=os.path.join(OUT,'fx',name); os.makedirs(d,exist_ok=True)
open(d+'/m.ll','w').write('\n'.join(L)+'\n'+'\n'.join(extra)+'\n')
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(json.dumps({'name':name,'err':r.stderr[-400:]})); sys.exit(1)
c=oracle.elf_fn(d+'/m.o',oracle.KEEP); os.remove(d+'/m.o'); open(d+'/fn.bin','wb').write(c)
ot=oracle.mask(oracle.orig_window()); ct=oracle.mask(c)
sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False); M=sum(x.size for x in sm.get_matching_blocks())
print(json.dumps({'name':name,'M':M,'ratio':round(2*M/(len(ot)+len(ct)),5),'bytes':len(c),'sig':hashlib.sha1(b''.join(ct)).hexdigest()[:12]}))
