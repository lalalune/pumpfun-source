#!/usr/bin/env python3
"""screen_post.py <m.ll> <edits.jsonl> <out.jsonl> [workers] [--combo f] [--base-sig s --base-M m]: llc-only screen of post-opt edits."""
import sys,os,json,time,hashlib,subprocess,shutil
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
A=sys.argv[1:]
def opt(k,d=None): return A[A.index(k)+1] if k in A else d
BSIG=opt('--base-sig'); BM=int(opt('--base-M','0'))
sys.argv=[sys.argv[0]]
import fx, oracle, screen
L=None; E=None
def init(base,ef):
    global L,E
    L=open(base).read().split('\n'); E={}
    for l in open(ef):
        e=json.loads(l); E[e['id']]=e
def run1(ids):
    k='+'.join(ids); t=screen.apply(L,[E[i] for i in ids])
    if t is None: return {'id':k,'err':'conflict'}
    t=t.replace('!990001 = !{!"branch_weights", i32 2000, i32 1}\n!990002 = !{!"branch_weights", i32 1, i32 2000}\n','')
    nm='q'+hashlib.sha1(k.encode()).hexdigest()[:10]; d=os.path.join(fx.OUT,'fx',nm); os.makedirs(d,exist_ok=True); t0=time.time()
    try:
        open(d+'/m.ll','w').write(t)
        r=subprocess.run(['nice','-n','5',fx.LLC,*fx.LLCA,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
        if r.returncode: return {'id':k,'err':'llc:'+r.stderr[-300:]}
        b=oracle.elf_fn(d+'/m.o',oracle.KEEP); sig=hashlib.sha1(b''.join(oracle.mask(b))).hexdigest()[:12]
        M=BM if (BSIG and sig==BSIG) else fx.Mof(b)[0]
        return {'id':k,'M':M,'bytes':len(b),'secs':round(time.time()-t0,1),'sig':sig}
    finally: shutil.rmtree(d,ignore_errors=True)
def main():
    base,ef,outf=A[0],A[1],A[2]; W=int(A[3]) if len(A)>3 and not A[3].startswith('--') else 4
    init(base,ef); done=set()
    if os.path.exists(outf):
        for l in open(outf):
            try: done.add(json.loads(l)['id'])
            except Exception: pass
    if '--combo' in A: jobs=[l.split() for l in open(opt('--combo')) if l.split() and '+'.join(l.split()) not in done]
    else: jobs=[[i] for i in E if i not in done]
    print(len(jobs),'jobs',flush=True)
    with Pool(W,initializer=init,initargs=(base,ef)) as p, open(outf,'a') as f:
        for r in p.imap_unordered(run1,jobs,chunksize=1): f.write(json.dumps(r)+'\n'); f.flush()
if __name__=='__main__': main()
