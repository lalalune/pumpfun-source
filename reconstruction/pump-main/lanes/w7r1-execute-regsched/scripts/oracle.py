#!/usr/bin/env python3
"""oracle.py <ll> <name> [edit.py] : (optionally edit) extract sweep fn, llc, diff vs original normalized."""
import sys,subprocess,re,os,runpy,difflib
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-regsched')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
ll,name=sys.argv[1],sys.argv[2]
d=OUT+'/irexp/'+name; os.makedirs(d,exist_ok=True)
t=open(ll).read()
m=re.search(r'define [^\n]*@(_ZN14pump_recovered5sweep7execute17h[0-9a-f]+E)',t); SYM=m.group(1)
if len(sys.argv)>3:
    t2=runpy.run_path(sys.argv[3])['edit'](t); assert t2!=t,'edit changed nothing'; t=t2
open(d+'/m.ll','w').write(t)
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
fn=subprocess.run(['sh',OUT+'/scripts/fn.sh',d+'/m.o',SYM],capture_output=True,text=True).stdout
fn=re.sub(r'call -?0x[0-9a-f]+','call X',fn); fn=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',fn)
open(d+'/fn.txt','w').write(fn)
o=open(OUT+'/sweep-orig-norm.txt').read().splitlines(); c=fn.splitlines()
sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
diff=[l for l in difflib.unified_diff(o,c,'orig','cand',n=1,lineterm='')]
nd=sum(1 for l in diff if l[:1] in '+-' and l[:3] not in('+++','---'))
def mask(L): return [re.sub(r'r10 - 0x[0-9a-f]+','r10-S',re.sub(r'\br[0-9]\b','r',x)) for x in L]
sm2=difflib.SequenceMatcher(None,mask(o),mask(c),autojunk=False)
print(f'{name}: struct={sm2.ratio():.4f} insns orig={len(o)} cand={len(c)} difflines={nd} ratio={sm.ratio():.4f} calls={sum("call" in x for x in c)}')
if '-v' in os.environ.get('V',''): print('\n'.join(diff[:80]))
