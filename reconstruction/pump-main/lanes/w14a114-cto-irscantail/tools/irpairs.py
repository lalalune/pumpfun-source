#!/usr/bin/env python3
"""irpairs.py <mn.ll> <scan.jsonl> <out.jsonl> <minM> [maxreps]: pairwise combos of distinct near-neutral single moves."""
import sys,json,os,tempfile,itertools
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
sys.argv_saved=sys.argv; 
import importlib.util
import px2
exec(open(T+'/irscan.py').read().split("src,outf=sys.argv")[0])
src,scan,outf,minM=sys.argv[1:5]; MX=int(sys.argv[5]) if len(sys.argv)>5 else 80
H,BL,TL=load(open(src).read())
R=[json.loads(l) for l in open(scan)]; R=[r for r in R if 'M' in r and r['M']>=int(minM)]
B=None
sig={}
for r in sorted(R,key=lambda r:(-r['M'],abs(r['bytes']-27400))):
    k=(r['M'],r['bytes'],json.dumps(r['ch'],sort_keys=True))
    if k not in sig: sig[k]=r
reps=list(sig.values())
base=[r for r in reps if r['M']==2245 and r['bytes']==27400]
reps=[r for r in reps if r not in base][:MX]
jobs=list(itertools.combinations(range(len(reps)),2))
def run(j):
    a,b=reps[j[0]],reps[j[1]]
    try:
        bl=move(BL,a['u'].split('+'),a['p']); bl=move(bl,b['u'].split('+'),b['p'])
    except Exception as e: return None
    with tempfile.TemporaryDirectory(dir=os.environ.get('TMPD')) as d:
        f=d+'/t.ll'; open(f,'w').write(dump(H,bl,TL)); r=px2.run(f)
    return {'a':a['u']+'@'+a['p'],'b':b['u']+'@'+b['p'],'Ma':a['M'],'Mb':b['M'],**r}
if __name__=='__main__':
    print(len(reps),'reps',len(jobs),'jobs',flush=True)
    if os.environ.get('COUNT'): sys.exit()
    with Pool(int(os.environ.get('NP','5'))) as P, open(outf,'w') as f:
        for r in P.imap_unordered(run,jobs,chunksize=2):
            if r: f.write(json.dumps(r)+'\n'); f.flush()
