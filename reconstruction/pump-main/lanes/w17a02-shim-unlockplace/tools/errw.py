#!/usr/bin/env python3
# errw.py <m.ll> <a> <b> [region-regex]: put weight a:b (toward the error successor = a) on every br whose successor block
# calls PumpError::name within its first 12 lines; llc; print M/bytes. Experiment only.
import sys,os,re,subprocess,difflib,tempfile
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a06-cto-bonoutline/tools')
import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src,a,b=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]); rx=re.compile(sys.argv[4]) if len(sys.argv)>4 else None
L=open(src).read().split('\n')
st=[i for i,l in enumerate(L) if l.startswith('define ') and re.search(oracle.KEEP,l)][0]
en=st+[i for i,l in enumerate(L[st:]) if l=='}'][0]
lab={}
for i in range(st,en):
    m=re.match(r'^("?[^\s:"]+"?):',L[i])
    if m: lab[m.group(1).strip('"')]=i
def errblk(name):
    i=lab.get(name.strip('"'))
    if i is None: return False
    return any('PumpError4name' in L[k] for k in range(i,min(i+14,en)))
n=0; extra=[]
for i in range(st,en):
    m=re.match(r'(\s+br i1 %[\w.]+, label %("?[^,"]+"?), label %("?[^,"]+"?))$',L[i])
    if not m: continue
    t,f=m.group(2),m.group(3)
    if rx and not (rx.search(t) or rx.search(f)): continue
    et,ef=errblk(t),errblk(f)
    if et==ef: continue
    w=(a,b) if et else (b,a)
    L[i]=L[i]+', !prof !9988%d'%n; extra.append('!9988%d = !{!"branch_weights", i32 %d, i32 %d}'%(n,w[0],w[1])); n+=1
d=tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(src)))
open(d+'/m.ll','w').write('\n'.join(L+extra)+'\n')
r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
if r.returncode: print(r.stderr[-400:]); sys.exit(1)
c=oracle.elf_fn(d+'/m.o',oracle.KEEP); o=oracle.mask(oracle.orig_window()); ct=oracle.mask(c)
sm=difflib.SequenceMatcher(None,o,ct,autojunk=False); M=sum(x.size for x in sm.get_matching_blocks())
print('edges',n,'w',a,b,'bytes',len(c),'M',M)
subprocess.run(['rm','-rf',d])
