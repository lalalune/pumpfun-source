#!/usr/bin/env python3
"""ora.py <ll> [edit.py]: llc the (optionally edited) module, diff buy_handler vs original (normalized)."""
import sys,subprocess,re,os,runpy,difflib,tempfile
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-buyhandler-coords')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
S=os.path.dirname(os.path.abspath(__file__))
ll=sys.argv[1]; t=open(ll).read()
SYM=re.search(r'@(_ZN14pump_recovered6buy_v211buy_handler17h[0-9a-f]+E)\(',t).group(1)
args=[a for a in sys.argv[1:] if a!="-v"]
if len(args)>1:
    ns=runpy.run_path(args[1]); t2=ns['edit'](t); assert t2!=t,'edit changed nothing'
    d=tempfile.mkdtemp(dir=O+'/tmp'); p=d+'/m.ll'; open(p,'w').write(t2)
else:
    d=os.path.dirname(ll); p=ll
r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',p,'-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
fn=subprocess.run([S+'/fn.sh',d+'/m.o',SYM],capture_output=True,text=True).stdout
fn=re.sub(r'call -?0x[0-9a-f]+','call X',fn); fn=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',fn)
fn=re.sub(r'\s+',' ',fn.replace('\n','\x00')).replace('\x00','\n') if False else fn
c=[re.sub(r'\s+',' ',x).strip() for x in fn.splitlines() if x.strip()]
o=[re.sub(r'\s+',' ',x).strip() for x in open(O+'/orig-norm.txt').read().splitlines()]
open(d+'/fn.txt','w').write('\n'.join(c)+'\n')
diff=[l for l in difflib.unified_diff(o,c,'orig','cand',n=1,lineterm='')]
nd=sum(1 for l in diff if l[:1] in '+-' and l[:3] not in('+++','---'))
print(f'insns orig={len(o)} cand={len(c)} difflines={nd} dir={d}')
if '-v' in sys.argv: print('\n'.join(diff[:200]))
