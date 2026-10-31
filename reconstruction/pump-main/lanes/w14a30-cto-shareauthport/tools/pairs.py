#!/usr/bin/env python3
"""pairs.py <mn.ll> <dir> <K> clones...: for every pair of clones, llc-score all combos of each clone's top-K jobs (from <dir>/<clone>_p*.jsonl)."""
import sys,os,json,glob,subprocess,itertools,tempfile
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g); ORIG=g['orig_window']()
mll,D,K=sys.argv[1],sys.argv[2],int(sys.argv[3]); C=sys.argv[4:]
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
top={}
for c in C:
    n=c.strip('%').replace('.','')
    R={}
    for f in glob.glob('%s/%s_p*.jsonl'%(D,n)):
        for l in open(f):
            r=json.loads(l)
            if r.get('bytes')==27400 and ':' in r['lab']: R[r['lab']]=r['ratio']
    seen=set(); top[c]=[]
    for k in sorted(R,key=lambda k:-R[k]):
        key=(k.split(':')[0],R[k])
        if key in seen: continue
        seen.add(key); top[c].append(k)
        if len(top[c])>=K: break
def score(p):
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',p+'.o'],capture_output=True)
    if r.returncode: return None
    c=g['elf_fn'](p+'.o',g['KEEP']); rr,sd=g['metric'](c,ORIG); return round(rr,5),len(c),sd
def job(args):
    a,ja,b,jb=args; d=tempfile.mkdtemp(dir=D)
    e=dict(os.environ,MODE='dump',XVAL=a,JOB=ja); subprocess.run(['python3',T+'/pscan.py',mll,'x',d+'/1.ll'],env=e,capture_output=True)
    e=dict(os.environ,MODE='dump',XVAL=b,JOB=jb); subprocess.run(['python3',T+'/pscan.py',d+'/1.ll','x',d+'/2.ll'],env=e,capture_output=True)
    s=score(d+'/2.ll') if os.path.exists(d+'/2.ll') else None; subprocess.run(['rm','-rf',d])
    return {'a':a,'ja':ja,'b':b,'jb':jb,'res':s}
jobs=[(a,ja,b,jb) for a,b in itertools.combinations(C,2) for ja in top[a] for jb in top[b]]
with ThreadPoolExecutor(4) as ex, open(D+'/'+os.environ.get('PNAME','pairs')+'.jsonl','w') as f:
    for r in ex.map(job,jobs): f.write(json.dumps(r)+'\n'); f.flush()
