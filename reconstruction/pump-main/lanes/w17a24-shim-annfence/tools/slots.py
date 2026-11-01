#!/usr/bin/env python3
"""slots.py <base.ll> <edits.jsonl> <ids-file> <out.jsonl> [workers]: oracle M + masked positional slots_diff for each id line."""
import sys,os,json,hashlib,subprocess,shutil
import multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
G={}
def run(ids):
    import fx, oracle, screen
    L,E,ob=G['L'],G['E'],G['ob']
    k='+'.join(ids)
    t='\n'.join(L) if ids==['BASE'] else screen.apply(L,[E[i] for i in ids])
    if t is None: return {'id':k,'err':'conflict'}
    nm='s'+hashlib.sha1(k.encode()).hexdigest()[:10]; d=os.path.join(fx.OUT,'fx',nm); os.makedirs(d,exist_ok=True)
    try:
        open(d+'/in.ll','w').write(t)
        subprocess.run(['nice','-n','5',fx.OPT,'-O3',d+'/in.ll','-S','-o',d+'/o3.ll'],capture_output=True)
        open(d+'/m.ll','w').write(oracle.slim(open(d+'/o3.ll').read()))
        subprocess.run(['nice','-n','5',fx.LLC,*fx.LLCA,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True)
        b=oracle.elf_fn(d+'/m.o',oracle.KEEP); cb=b''.join(oracle.mask(b))
        sd=sum(1 for i in range(0,len(ob),8) if ob[i:i+8]!=cb[i:i+8]) if len(ob)==len(cb) else None
        M,_=fx.Mof(b)
        return {'id':k,'M':M,'bytes':len(b),'slots':sd,'sig':hashlib.sha1(cb).hexdigest()[:12]}
    finally: shutil.rmtree(d,ignore_errors=True)
def main():
    base,ef,idf,outf=sys.argv[1:5]; W=int(sys.argv[5]) if len(sys.argv)>5 else 4
    import oracle
    G['L']=open(base).read().split('\n'); G['E']={json.loads(l)['id']:json.loads(l) for l in open(ef)}
    G['ob']=b''.join(oracle.mask(oracle.orig_window()))
    jobs=[l.split() for l in open(idf) if l.strip()]
    with mp.Pool(W) as p, open(outf,'a') as f:
        for r in p.imap_unordered(run,jobs): f.write(json.dumps(r)+'\n'); f.flush()
if __name__=='__main__':
    mp.set_start_method('fork'); main()
