#!/usr/bin/env python3
"""prof.py <m.ll> <name> <brsubstr>=<a>:<b> ...: add !prof branch_weights to the unique br line containing brsubstr, llc, score (sc.py) + seq"""
import sys,re,subprocess,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import sc
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src,name=sys.argv[1],sys.argv[2]; t=open(src).read()
for k,spec in enumerate(sys.argv[3:]):
    sub,w=spec.rsplit('=',1); a,b=w.split(':')
    L=t.split('\n'); idx=[i for i,l in enumerate(L) if l.strip().startswith('br i1') and sub in l]
    assert len(idx)==1,(sub,len(idx))
    l=re.sub(r', !prof !\d+','',L[idx[0]]); L[idx[0]]=l+f', !prof !{9000000+k}'
    t='\n'.join(L)+f'\n!{9000000+k} = !{{!"branch_weights", i32 {a}, i32 {b}}}\n'
d=os.path.dirname(os.path.dirname(T))+'/w14a104-cto-brhead/tmp/p'; os.makedirs(d,exist_ok=True)
open(f'{d}/{name}.ll','w').write(t)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',f'{d}/{name}.ll','-filetype=asm','-o',f'{d}/{name}.s'],capture_output=True,text=True)
if r.returncode: sys.exit(r.stderr[-2000:])
s=sc.score(f'{d}/{name}.s'); s.pop('ch'); print(name,json.dumps(s))
