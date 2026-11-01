#!/usr/bin/env python3
"""screenp.py <base.ll> <edits.jsonl> <out.jsonl> [workers] [kinds] [--combo file] [--base-sig SIG --base-M M]:
process-pool version of w17a06 screen.py (no GIL serialisation); skips the LCS when the masked output equals the base."""
import sys,os,json,time,hashlib,difflib,subprocess
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import fx, oracle, screen
A=sys.argv[1:]
def opt(k,d=None):
    return A[A.index(k)+1] if k in A else d
BSIG=opt('--base-sig'); BM=int(opt('--base-M','0'))
L=None; E=None
SC={}
def init(base,ef):
    global L,E,SC
    L=open(base).read().split('\n'); E={}
    for l in open(ef):
        e=json.loads(l); E[e['id']]=e
    import glob
    for p in glob.glob(fx.OUT+'/res/*.jsonl')+glob.glob(fx.OUT+'/b/*.jsonl'):
        try:
            for l in open(p):
                try:
                    r=json.loads(l)
                    if 'M' in r and 'sig' in r: SC[r['sig']]=(r['M'],r['bytes'])
                except Exception: pass
        except Exception: pass
def run1(ids):
    t=screen.apply(L,[E[i] for i in ids])
    k='+'.join(ids)
    if t is None: return {'id':k,'err':'conflict'}
    nm='p'+hashlib.sha1(k.encode()).hexdigest()[:10]
    d=os.path.join(fx.OUT,'fx',nm); os.makedirs(d,exist_ok=True); t0=time.time()
    try:
        open(d+'/in.ll','w').write(t)
        r=subprocess.run(['nice','-n','5',fx.OPT,'-O3',d+'/in.ll','-S','-o',d+'/o3.ll'],capture_output=True,text=True)
        if r.returncode: return {'id':k,'err':'opt:'+r.stderr[-300:]}
        m=oracle.slim(open(d+'/o3.ll').read()); open(d+'/m.ll','w').write(m)
        r=subprocess.run(['nice','-n','5',fx.LLC,*fx.LLCA,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
        if r.returncode: return {'id':k,'err':'llc:'+r.stderr[-300:]}
        b=oracle.elf_fn(d+'/m.o',oracle.KEEP)
        sig=hashlib.sha1(b''.join(oracle.mask(b))).hexdigest()[:12]
        if BSIG and sig==BSIG: M=BM
        elif sig in SC and SC[sig][1]==len(b): M=SC[sig][0]
        else: M,_=fx.Mof(b)
        n=len(oracle.mask(b))
        return {'id':k,'M':M,'ratio':round(2*M/(3339+n),5),'bytes':len(b),'secs':round(time.time()-t0,1),'sig':sig}
    finally:
        import shutil; shutil.rmtree(d,ignore_errors=True)
def main():
    base,ef,outf=A[0],A[1],A[2]; W=int(A[3]) if len(A)>3 and not A[3].startswith('--') else 4
    kinds=A[4].split(',') if len(A)>4 and not A[4].startswith('--') and A[4]!='-' else None
    init(base,ef)
    done=set()
    if os.path.exists(outf):
        for l in open(outf):
            try: done.add(json.loads(l)['id'])
            except Exception: pass
    if '--combo' in A:
        jobs=[l.split() for l in open(opt('--combo')) if l.split() and '+'.join(l.split()) not in done]
    else:
        jobs=[[i] for i,e in E.items() if i not in done and (kinds is None or e['kind'] in kinds)]
        if kinds:
            pri={k:n for n,k in enumerate(kinds)}; jobs.sort(key=lambda j:pri.get(E[j[0]]['kind'],99))
    print(len(jobs),'jobs',flush=True)
    with Pool(W,initializer=init,initargs=(base,ef)) as p, open(outf,'a') as f:
        for r in p.imap_unordered(run1,jobs,chunksize=1):
            f.write(json.dumps(r)+'\n'); f.flush()
if __name__=='__main__': main()
