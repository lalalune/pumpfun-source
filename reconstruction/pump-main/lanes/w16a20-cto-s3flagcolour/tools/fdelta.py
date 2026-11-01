#!/usr/bin/env python3
"""fdelta.py <m.ll> <force|-> <out.jsonl> [N] [deltas]: single spill-weight deltas under RAPRIO_FORCE (sticky) with the
join-restore (llcw.py), exact SSC colours (experiment only). For each of the N heaviest spill intervals and each delta d
(SSC_WSET ss:+d, or ss:=v for '=v'), prints M and bytes."""
import sys,os,json,re,subprocess,tempfile,difflib
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import flagcol as F, oracle
OUT=os.path.dirname(T); LLC=OUT+'/llvmb/bin/llc'
ll,force,outf=sys.argv[1:4]; N=int(sys.argv[4]) if len(sys.argv)>4 else 40
deltas=(sys.argv[5] if len(sys.argv)>5 else '+1,+0.375,-0.375,=0.0005').split(',')
env0=dict(os.environ); env0['RAPRIO_STICKY']='1'
if force!='-': env0['RAPRIO_FORCE']=force
p=subprocess.run([LLC,*F.A,ll,'-filetype=obj','-o','/dev/null','-debug-only=stack-slot-coloring'],env=env0,capture_output=True,text=True)
iv,asg=F.parse(p.stderr)
top=sorted(iv,key=lambda s:-iv[s])[:N]
O=oracle.orig_window(); OM=oracle.mask(O)
def one(spec):
    env=dict(env0)
    if spec!='-': env['SSC_WSET']=spec
    fd,obj=tempfile.mkstemp(suffix='.o',dir=OUT+'/an'); os.close(fd)
    q=subprocess.run([sys.executable,T+'/llcw.py',*F.A,ll,'-filetype=obj','-o',obj],env=env,capture_output=True,text=True)
    if q.returncode: os.remove(obj); return spec,None,None
    b=oracle.elf_fn(obj,oracle.KEEP); os.remove(obj)
    sm=difflib.SequenceMatcher(None,OM,oracle.mask(b),autojunk=False)
    return spec,sum(x.size for x in sm.get_matching_blocks()),len(b)
specs=['-']
for s in top:
    for d in deltas:
        specs.append(f'{s}:{d}' if d[0]=='=' else f'{s}:{d}')
with open(outf,'w') as f, ThreadPoolExecutor(int(os.environ.get('J','4'))) as ex:
    for spec,M,by in ex.map(one,specs):
        ss=int(spec.split(':')[0]) if spec!='-' else None
        f.write(json.dumps({'spec':spec,'w':iv.get(ss),'rank':top.index(ss) if ss in top else None,'M':M,'bytes':by})+'\n'); f.flush()
