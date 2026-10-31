# beam.py <mn.ll> <singles.jsonl> <out.jsonl> [target_bytes] : beam over reload2 ops toward the pinned size
import sys,os,json,subprocess
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__))
mll,sj,out=sys.argv[1:4]; TB=int(sys.argv[4]) if len(sys.argv)>4 else 27400
src=open(T+'/reload2.py').read().split("adds=[]")[0]
sys.argv=['x',mll,out]; G={'__file__':T+'/reload2.py'}; exec(src,G)
S=[json.loads(l) for l in open(sj)]; base=min(S,key=lambda r:0)  # unused
cand=[r['lab'] for r in S if 'M' in r and r['bytes']>int(os.environ.get('BASEB','27360'))]
cand=sorted(cand,key=lambda l:-next(r['M'] for r in S if r['lab']==l))[:int(os.environ.get('K','20'))]
ops={l:G['parse'](l)[0] for l in cand}
beam=[((),None)]; seen=set(); allres=[]
f=open(out,'w')
for rnd in range(int(os.environ.get('R','5'))):
    jobs=[]
    for st,_ in beam:
        for l in cand:
            if l in st: continue
            ns=tuple(sorted(st+(l,)))
            if ns in seen: continue
            seen.add(ns); jobs.append(ns)
    with ThreadPoolExecutor(4) as ex: res=list(ex.map(lambda ns:(ns,G['run']([ops[x] for x in ns])),jobs))
    for ns,r in res: f.write(json.dumps(r)+'\n'); allres.append(r)
    f.flush()
    ok=[(ns,r) for ns,r in res if 'M' in r and r['bytes']<=TB]
    hit=[r for ns,r in res if r.get('bytes')==TB]
    hit.sort(key=lambda r:-r['M']); print('round',rnd,len(jobs),'best@TB',hit[:3],flush=True)
    ok.sort(key=lambda z:-z[1]['M']); beam=ok[:int(os.environ.get('W','10'))]
