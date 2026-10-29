#!/usr/bin/env python3
"""swapscan.py base.ll outjson [range]: try all adjacent independent instruction swaps in target fn; report diffslots."""
import sys,re,subprocess,difflib,os,json,tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
OUT=Path(__file__).resolve().parent.parent
B=Path.home()/'.cache/solana/v1.44/platform-tools/llvm/bin'
base=sys.argv[1]; t=open(base).read()
m=re.search(r'^define[^\n]*create_token_account_v217h[^\n]*\n.*?^\}\n',t,re.M|re.S)
pre,fn,post=t[:m.start()],m.group(0),t[m.end():]
L=fn.split('\n')
o=(OUT/'llc/orig.n').read_text().splitlines()
def score(lines):
    fd,p=tempfile.mkstemp(suffix='.ll',dir='/private/tmp/claude-501'); os.close(fd)
    open(p,'w').write(pre+'\n'.join(lines)+post)
    ob=p+'.o'
    r=subprocess.run([str(B/'llc'),'-O3','-filetype=obj','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',p,'-o',ob],capture_output=True,text=True)
    os.unlink(p)
    if r.returncode: return None
    a=subprocess.run([str(OUT/'tools/disobj.sh'),ob],capture_output=True,text=True).stdout.splitlines(); os.unlink(ob)
    sm=difflib.SequenceMatcher(None,o,a,autojunk=False)
    return sum(max(i2-i1,j2-j1) for t_,i1,i2,j1,j2 in sm.get_opcodes() if t_!='equal'),round(sm.ratio(),4),len(a)
def isins(l):
    s=l.strip()
    return l.startswith('  ') and s and not s.startswith(';') and not s.startswith('br ') and not s.startswith('ret ') and not s.startswith('unreachable') and not s.startswith('switch') and 'phi ' not in s
def defs(l):
    mm=re.match(r'\s+(%[\w.$"\-]+) =',l); return mm.group(1) if mm else None
cands=[]
lo,hi=(0,len(L))
if len(sys.argv)>3: lo,hi=map(int,sys.argv[3].split(','))
for i in range(max(1,lo),min(hi,len(L)-1)):
    a,b=L[i],L[i+1]
    if not(isins(a) and isins(b)): continue
    d=defs(a)
    if d and re.search(re.escape(d)+r'(?![\w.])',b): continue
    if 'noalias.scope.decl' in a or 'noalias.scope.decl' in b: continue
    cands.append(i)
base_s=score(L); print('base',base_s,'cands',len(cands),flush=True)
def run(i):
    L2=L[:]; L2[i],L2[i+1]=L2[i+1],L2[i]; return i,score(L2)
res=[]
with ThreadPoolExecutor(8) as ex:
    for i,s in ex.map(run,cands):
        if s and s[0]!=base_s[0]: res.append((s[0],s[1],s[2],i,L[i].strip()[:90],L[i+1].strip()[:90]))
res.sort()
json.dump({'base':base_s,'res':res},open(sys.argv[2],'w'),indent=0)
for r in res[:30]: print(r)
