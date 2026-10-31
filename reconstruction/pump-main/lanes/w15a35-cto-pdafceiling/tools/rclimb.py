#!/usr/bin/env python3
"""rclimb.py <m.ll> <pool.jsonl> <out.log> [rounds=6] [base_json] [nproc=6]: rescreen climb. Each round scores
base+s for EVERY single s of the pool (not just the top-K of the base screen) and keeps the best if it raises M.
This is the w15a18 cl_U whole-pool rescreen, on the light fscr cell."""
import sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fscr, multiprocessing as mp
from fclimb import comb,KEYS
def main():
    m,pf,of=sys.argv[1:4]; R=int(sys.argv[4]) if len(sys.argv)>4 else 6
    base=json.loads(sys.argv[5]) if len(sys.argv)>5 and sys.argv[5] else {}; npr=int(sys.argv[6]) if len(sys.argv)>6 else 6
    P=[json.loads(l) for l in open(pf)]
    cur={k:base[k] for k in KEYS if base.get(k)}; cur['name']=base.get('name','base')
    log=open(of,'a')
    if True:
        best=fscr.prun([(m,cur)],1)[0]; print('start',best.get('M'),best.get('bytes'),flush=True)
        used=set(base.get('used',[]))
        for r in range(R):
            jobs=[]
            for s in P:
                if s['name'] in used: continue
                j=comb({k:cur[k] for k in KEYS if cur.get(k)},s); j['name']=cur['name']+'+'+s['name']; j['add']=s['name']; jobs.append((m,j))
            res=[x for x in fscr.prun(jobs,npr) if 'M' in x]; res.sort(key=lambda x:(-x['M'],abs(x['bytes']-27400)))
            for x in res[:5]: print(f"  r{r} {x['add']:14s} M {x['M']} bytes {x['bytes']}",flush=True)
            log.write(json.dumps({'round':r,'base':cur['name'],'top':[{k:x[k] for k in ('add','M','bytes')} for x in res[:20]]})+'\n'); log.flush()
            if not res or res[0]['M']<=best['M']: print('stop',flush=True); break
            best=res[0]; cur={k:best[k] for k in KEYS if best.get(k)}; cur['name']=best['name']; used.add(best['add'])
            print(f"step {r}: +{best['add']} -> M {best['M']} bytes {best['bytes']} ratio {best['ratio']}",flush=True)
    print('FINAL',json.dumps(best),flush=True)
if __name__=='__main__': main()
