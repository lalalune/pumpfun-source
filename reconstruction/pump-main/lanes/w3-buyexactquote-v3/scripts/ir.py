#!/usr/bin/env python3
"""ir.py <name> [edit.py|-] : apply edit(text)->text to base IR (IRBASE), llc, diff buy_exact_quote vs original."""
import sys,subprocess,re,os,runpy,difflib
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w3-buyexactquote-v3')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
SYM=os.environ.get('SYM','_ZN14pump_recovered5trade15buy_exact_quote17h729b305ff0379d4dE')
name=sys.argv[1]; edit=sys.argv[2] if len(sys.argv)>2 else '-'
base=os.environ.get('IRBASE',OUT+'/out/ir-base/pump_recovered.ll')
t=open(base).read()
if edit!='-':
    ns=runpy.run_path(edit); t2=ns['edit'](t); assert t2!=t,'edit changed nothing'
else: t2=t
d=OUT+'/irexp/'+name; os.makedirs(d,exist_ok=True)
open(d+'/m.ll','w').write(t2)
r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
fn=subprocess.run([OUT+'/scripts/fn.sh',d+'/m.o',SYM],capture_output=True,text=True).stdout
def norm(s):
    s=re.sub(r'call -?0x[0-9a-f]+','call X',s); s=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',s); return s
fn="\n".join(norm(x).strip() for x in fn.splitlines() if x.strip())+"\n"
open(d+'/fn.txt','w').write(fn)
o=open(OUT+'/an/orig-norm.txt').read().splitlines(); c=fn.splitlines()
sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
ds=sum(max(i2-i1,j2-j1) for tg,i1,i2,j1,j2 in sm.get_opcodes() if tg!='equal')
print(f'{name}: insns orig={len(o)} cand={len(c)} diffslots={ds} ratio={sm.ratio():.4f}')
if os.environ.get('SHOW'):
    diff=[l for l in difflib.unified_diff(o,c,'orig','cand',n=1,lineterm='')]
    print('\n'.join(diff[:int(os.environ.get('SHOW'))]))
def mask(s):
    s=re.sub(r'\br\d\b','r',s); s=re.sub(r'r10 - 0x[0-9a-f]+','S',s)
    if s.startswith('j'): s=re.sub(r'[+-]0x[0-9a-f]+$','OFF',s)
    return s
mo=[mask(x) for x in o]; mc=[mask(x) for x in c]
sm2=difflib.SequenceMatcher(None,mo,mc,autojunk=False)
ds2=sum(max(i2-i1,j2-j1) for tg,i1,i2,j1,j2 in sm2.get_opcodes() if tg!='equal')
print(f'   masked: diffslots={ds2} ratio={sm2.ratio():.4f}')
