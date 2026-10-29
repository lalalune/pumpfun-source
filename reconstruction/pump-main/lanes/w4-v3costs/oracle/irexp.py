#!/usr/bin/env python3
"""Diagnostic only. irexp.py <name> <edit.py|-> [llc args]: edit(fn_text)->fn_text on v3_buy_costs IR in base module, llc, diff vs original."""
import sys,subprocess,re,os,runpy,difflib
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-v3costs')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
base=os.environ.get('IRBASE',OUT+'/ir/base/one.ll')
name,edit=sys.argv[1],sys.argv[2]
t=open(base).read()
m=re.search(r'^define[^\n]*12v3_buy_costs[^\n]*\{\n.*?^\}\n',t,re.M|re.S)
sym=re.search(r'@(\S+?)\(',m.group(0)).group(1)
f=m.group(0)
if edit!='-':
    f2=runpy.run_path(edit)['edit'](f); assert f2!=f,'edit changed nothing'
else: f2=f
t2=t[:m.start()]+f2+t[m.end():]
d=OUT+'/irexp/'+name; os.makedirs(d,exist_ok=True)
open(d+'/fn.ll','w').write(f2); open(d+'/m.ll','w').write(t2)
r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/m.ll','-filetype=obj','-o',d+'/m.o']+sys.argv[3:],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
fn=subprocess.run(['sh',OUT+'/bin/fn.sh',d+'/m.o',sym],capture_output=True,text=True).stdout
fn=re.sub(r'call -?0x[0-9a-f]+','call X',fn); fn=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',fn)
c=[re.sub(r'([+-]0x[0-9a-f]+)$','J',l.strip()) if re.match(r'(ja|j[a-z]+ )',l.strip()) else l.strip() for l in fn.splitlines()]; open(d+'/fn.txt','w').write('\n'.join(c)+'\n')
o=[re.sub(r'([+-]0x[0-9a-f]+)$','J',l.strip()) if re.match(r'(ja|j[a-z]+ )',l.strip()) else l.strip() for l in open(OUT+'/notes/orig-norm.txt').read().splitlines()]
diff=[l for l in difflib.unified_diff(o,c,'orig','cand',n=0,lineterm='')]
mi=sum(1 for l in diff if l[:1]=='-' and l[:3]!='---'); pl=sum(1 for l in diff if l[:1]=='+' and l[:3]!='+++')
sz=sum(16 if l.startswith('lddw') else 8 for l in c)
print(f'{name}: bytes={sz} lines orig={len(o)} cand={len(c)} -{mi} +{pl}')
if os.environ.get('V'): print('\n'.join(diff))
