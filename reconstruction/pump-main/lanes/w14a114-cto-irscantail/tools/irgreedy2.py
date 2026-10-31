#!/usr/bin/env python3
"""irgreedy2.py <mn.ll> <out.jsonl> <minM> scan.jsonl...: greedy accumulation of distinct single IR block moves (oracle bound)."""
import sys,json,os,tempfile
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import px2
exec(open(T+'/irscan.py').read().split("src,outf=sys.argv")[0])
src,outf,minM=sys.argv[1:4]; scans=sys.argv[4:]
H,BL,TL=load(open(src).read())
R=[json.loads(l) for f in scans for l in open(f)]; R=[r for r in R if 'M' in r and r['M']>=int(minM)]
sig={}
for r in sorted(R,key=lambda r:(-r['M'],abs(r['bytes']-27400))):
    k=(r['M'],r['bytes'],json.dumps(r['ch'],sort_keys=True))
    if k not in sig: sig[k]=r
reps=[(r['u'],r['p']) for r in sig.values() if not (r['M']==2245 and r['bytes']==27400)]
def apply(seq):
    bl=BL
    for u,p in seq: bl=move(bl,u.split('+'),p)
    return bl
def run(seq):
    try: bl=apply(seq)
    except Exception: return None
    with tempfile.TemporaryDirectory(dir=os.environ.get('TMPD')) as d:
        f=d+'/t.ll'; open(f,'w').write(dump(H,bl,TL)); r=px2.run(f)
    return {'seq':seq,**r}
if __name__=='__main__':
    cur=[tuple(x) for x in json.loads(os.environ.get('SEED','[]'))];best=2245; S=int(os.environ.get('SIZEPEN','0'))
    key=lambda r: r['M']-S*abs(r['bytes']-27400)/8
    bestk=float(os.environ.get('BESTK','2245'))
    print(len(reps),'reps',flush=True)
    with Pool(int(os.environ.get('NP','5'))) as P, open(outf,'w') as f:
        for step in range(12):
            cand=[cur+[m] for m in reps if m not in cur]
            res=[r for r in P.map(run,cand,chunksize=1) if r and 'M' in r]
            res.sort(key=lambda r:-key(r))
            top=res[0]; f.write(json.dumps({'step':step,'top':res[:5]})+'\n'); f.flush()
            print(step,top['M'],top['bytes'],top['ratio'],top['seq'][-1],flush=True)
            if key(top)<=bestk: break
            bestk=key(top); cur=top['seq']
