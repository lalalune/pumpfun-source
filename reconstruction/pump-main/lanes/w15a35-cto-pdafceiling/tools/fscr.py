#!/usr/bin/env python3
"""fscr.py <m.ll> <jobs.jsonl> <out.jsonl> [nproc] [--size-only]: light greedy screen (free cell only). Per job, run the private
RAPRIO llc once to an object with the job's prio/casc/weight/force env, cut admin_cto::execute, and record M (scorer
difflib masked tokens), ratio and bytes. Same job format as w15a18 scr.py; pinV/pinA are left to cell.sh for finalists."""
import sys,os,json,subprocess,tempfile,difflib,multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle
O=os.path.dirname(T); LLC=O+'/llvmb/bin/llc'
A=['-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections']
_OM=None
def om():
    global _OM
    if _OM is None: _OM=oracle.mask(oracle.orig_window())
    return _OM
def score(fn):
    o=om(); c=oracle.mask(fn)
    M=sum(b.size for b in difflib.SequenceMatcher(None,o,c,autojunk=False).get_matching_blocks())
    return M, round(2*M/(len(o)+len(c)),5)
def run(a):
    m,job=a; env=dict(os.environ)
    for k in list(env):
        if k.startswith('RAPRIO_'): env.pop(k)
    for k in ('prio','force','hint','casc','weight','nohint','sticky'):
        if job.get(k): env['RAPRIO_'+k.upper()]=job[k]
    fd,p=tempfile.mkstemp(suffix='.o',dir=O+'/tmp'); os.close(fd)
    r=subprocess.run([LLC,*A,m,'-filetype=obj','-o',p],env=env,capture_output=True,text=True)
    res=dict(job)
    if r.returncode: res['error']=r.stderr[-300:]
    else:
        fn=oracle.elf_fn(p,oracle.KEEP); M,rt=score(fn); res.update({'M':M,'ratio':rt,'bytes':len(fn)})
        if job.get('keep'): open(job['keep'],'wb').write(fn)
    os.remove(p); return res

def prun(args,n=6):
    """Robust parallel map of run() over args: survives killed workers (re-submits unfinished jobs on a fresh pool)."""
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from concurrent.futures.process import BrokenProcessPool
    todo=list(enumerate(args)); out={}
    for attempt in range(6):
        if not todo: break
        try:
            with ProcessPoolExecutor(n) as ex:
                fs={ex.submit(run,a):(i,a) for i,a in todo}
                for f in as_completed(fs):
                    i,a=fs[f]
                    try: out[i]=f.result()
                    except BrokenProcessPool: raise
                    except Exception as e: out[i]=dict(a[1],error=repr(e)[:200])
        except BrokenProcessPool:
            pass
        todo=[(i,a) for i,a in todo if i not in out]
    return [out[i] for i in range(len(args)) if i in out]
if __name__=='__main__':
    m,jf,of=sys.argv[1:4]; n=int(sys.argv[4]) if len(sys.argv)>4 else 6
    os.makedirs(O+'/tmp',exist_ok=True)
    done=set()
    if os.path.exists(of): done={json.loads(l)['name'] for l in open(of) if l.strip()}
    jobs=[json.loads(l) for l in open(jf) if l.strip()]; jobs=[j for j in jobs if j['name'] not in done]
    with mp.Pool(n) as p, open(of,'a') as f:
        for res in p.imap_unordered(run,[(m,j) for j in jobs]):
            f.write(json.dumps(res)+'\n'); f.flush()
