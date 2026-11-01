#!/usr/bin/env python3
"""dist.py <combos.txt> <out.jsonl> [workers]: for each combo (ids space-separated), apply to ir/m0.s.ll, run opt+llc,
and report M, bytes, sig and the distance from main (candidate tokens outside the difflib matching with main's
masked tokens). Experiment only."""
import sys,os,json,hashlib,subprocess,difflib,time,shutil
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import fx,oracle,screen
OUT=os.path.dirname(T)
L=None;E=None;MT=None
def init():
    global L,E,MT
    L=open(OUT+'/ir/m0.s.ll').read().split('\n'); E={}
    for l in open(OUT+'/gen/U.jsonl'):
        e=json.loads(l); E[e['id']]=e
    MT=oracle.mask(open(OUT+'/fx/main/fn.bin','rb').read())
def run1(ids):
    k='+'.join(ids); t=screen.apply(L,[E[i] for i in ids])
    if t is None: return {'id':k,'err':'conflict'}
    nm='d'+hashlib.sha1(k.encode()).hexdigest()[:10]; d=os.path.join(OUT,'fx',nm); os.makedirs(d,exist_ok=True)
    try:
        open(d+'/in.ll','w').write(t)
        r=subprocess.run(['nice','-n','5',fx.OPT,'-O3',d+'/in.ll','-S','-o',d+'/o3.ll'],capture_output=True,text=True)
        if r.returncode: return {'id':k,'err':'opt'}
        open(d+'/m.ll','w').write(oracle.slim(open(d+'/o3.ll').read()))
        r=subprocess.run(['nice','-n','5',fx.LLC,*fx.LLCA,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
        if r.returncode: return {'id':k,'err':'llc'}
        b=oracle.elf_fn(d+'/m.o',oracle.KEEP); c=oracle.mask(b)
        sig=hashlib.sha1(b''.join(c)).hexdigest()[:12]
        M,_=fx.Mof(b)
        sm=difflib.SequenceMatcher(None,MT,c,autojunk=False); mm=sum(x.size for x in sm.get_matching_blocks())
        return {'id':k,'M':M,'bytes':len(b),'sig':sig,'dist':len(c)-mm}
    finally: shutil.rmtree(d,ignore_errors=True)
if __name__=='__main__':
    a=sys.argv[1:]; W=int(a[2]) if len(a)>2 else 6
    jobs=[l.split() for l in open(a[0]) if l.split()]
    done=set()
    if os.path.exists(a[1]):
        for l in open(a[1]):
            try: done.add(json.loads(l)['id'])
            except Exception: pass
    jobs=[j for j in jobs if '+'.join(j) not in done]
    with Pool(W,initializer=init) as p, open(a[1],'a') as f:
        for r in p.imap_unordered(run1,jobs): f.write(json.dumps(r)+'\n'); f.flush()
