#!/usr/bin/env python3
"""screen.py <m.ll> <jobs.jsonl> <out.jsonl> [nproc]: run the private patched llc (RAPRIO_PRIO / RAPRIO_FORCE / RAPRIO_HINT
env per job) on one module and score ratio, slots, L1, L2 for admin_cto::execute. Experiment only.
job = {"name":..., "prio":"382=0xffffffff,...", "force":"0=r8", "hint":"..."}"""
import sys,os,json,subprocess,tempfile,difflib,multiprocessing as mp,types
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
src=open(T+'/rx.py').read(); g={'__name__':'x'}; exec(src.split("OUT=os.environ")[0],g)
C=types.ModuleType('C'); _s=open(T+'/cls.py').read(); C.__dict__['__file__']=T+'/cls.py'; exec(_s[:_s.index('def main')],C.__dict__)
LLC=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a84-cto-raprio/llvmb/bin/llc')
O=g['orig_window'](); OT=[g['mask'](O)]
def toks(raw,l): return [C.mask(t,l) for _,t in C.insns(raw)]
O1=toks(O,1); O2=toks(O,2)
bs=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
MM=g['mask'](g['elf_fn'](bs,g['KEEP']))
M=None; FULL=os.environ.get('SCREEN_FULL')=='1'
def run(job):
    env=dict(os.environ)
    for k in ('RAPRIO_PRIO','RAPRIO_FORCE','RAPRIO_HINT','RAPRIO_LOG'): env.pop(k,None)
    if job.get('prio'): env['RAPRIO_PRIO']=job['prio']
    if job.get('force'): env['RAPRIO_FORCE']=job['force']
    if job.get('hint'): env['RAPRIO_HINT']=job['hint']
    if job.get('log'): env['RAPRIO_LOG']=job['log']
    fd,o=tempfile.mkstemp(suffix='.o'); os.close(fd)
    r=subprocess.run([LLC,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',M,'-filetype=obj','-o',o,*job.get('args',[])],env=env,capture_output=True,text=True)
    res=dict(job)
    if r.returncode:
        if os.path.exists(o): os.remove(o)
        res['error']=r.stderr[-300:]; return res
    c=g['elf_fn'](o,g['KEEP'])
    if job.get('keep'): open(job['keep'],'wb').write(c)
    os.remove(o)
    rr,sd=g['metric'](c,O)
    res.update(ratio=round(rr,5),slots=sd,bytes=len(c),eq_main=g['mask'](c)==MM)
    if FULL or job.get('full'):
        res['L1']=round(difflib.SequenceMatcher(None,O1,toks(c,1),autojunk=False).ratio(),5)
        res['L2']=round(difflib.SequenceMatcher(None,O2,toks(c,2),autojunk=False).ratio(),5)
    return res
def init(m):
    global M; M=m
if __name__=='__main__':
    m,jf,of=sys.argv[1:4]; n=int(sys.argv[4]) if len(sys.argv)>4 else 4
    jobs=[json.loads(l) for l in open(jf) if l.strip()]
    with mp.Pool(n,initializer=init,initargs=(m,)) as p, open(of,'a') as f:
        for res in p.imap_unordered(run,jobs):
            f.write(json.dumps(res)+'\n'); f.flush()
