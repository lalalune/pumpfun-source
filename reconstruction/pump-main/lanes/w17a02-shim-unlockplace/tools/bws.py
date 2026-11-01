#!/usr/bin/env python3
# bws.py <m.ll> <outjsonl> [workers]: llc-only branch-weight sweep on a post-opt slim module of admin_cto::execute.
# Each run: one br gets !prof weights (a,b); llc; M against the original (oracle mask tokens).
import sys,os,re,subprocess,difflib,json,tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a06-cto-bonoutline/tools')
import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
src=open(sys.argv[1]).read(); outp=sys.argv[2]; nw=int(sys.argv[3]) if len(sys.argv)>3 else 3
W=[(20,12),(12,20),(2,1),(1,2),(1,2000),(2000,1)] if len(sys.argv)<=4 else [tuple(map(int,x.split(':'))) for x in sys.argv[4].split(',')]
lines=src.split('\n')
# BASEW="i:a:b;i:a:b" fixed weights applied to every run
FIX=[tuple(map(int,x.split(':'))) for x in os.environ.get('BASEW','').split(';') if x]
for k,(fi,fa,fb) in enumerate(FIX):
    lines[fi]=lines[fi]+', !prof !9999%d'%k
    lines.append('!9999%d = !{!"branch_weights", i32 %d, i32 %d}'%(k,fa,fb))
FIXI=set(f[0] for f in FIX)
# execute body
st=[i for i,l in enumerate(lines) if l.startswith('define ') and re.search(oracle.KEEP,l)][0]
en=st+[i for i,l in enumerate(lines[st:]) if l=='}'][0]
brs=[i for i in range(st,en) if re.match(r'\s+br i1 %[\w.]+, label %[\w.]+, label %[\w.]+$',lines[i]) and i not in FIXI]
otok=oracle.mask(oracle.orig_window())
def run(job):
    i,(a,b)=job
    L=list(lines); L[i]=L[i]+', !prof !99999'
    t='\n'.join(L)+'\n!99999 = !{!"branch_weights", i32 %d, i32 %d}\n'%(a,b)
    d=tempfile.mkdtemp(dir=os.path.dirname(outp))
    open(d+'/m.ll','w').write(t)
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: res={'i':i,'w':[a,b],'err':r.stderr[-300:]}
    else:
        c=oracle.elf_fn(d+'/m.o',oracle.KEEP); ct=oracle.mask(c)
        sm=difflib.SequenceMatcher(None,otok,ct,autojunk=False); M=sum(x.size for x in sm.get_matching_blocks())
        res={'i':i,'blk':lines[i].strip()[:80],'w':[a,b],'bytes':len(c),'M':M,'ntok':len(ct)}
    subprocess.run(['rm','-rf',d])
    return res
jobs=[(i,w) for i in brs for w in W]
if os.environ.get('BASEONLY'):
    jobs=jobs[:1]
with open(outp,'a') as f, ThreadPoolExecutor(nw) as ex:
    for res in ex.map(run,jobs):
        f.write(json.dumps(res)+'\n'); f.flush()
print('done',len(jobs))
