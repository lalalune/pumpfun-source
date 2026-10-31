#!/usr/bin/env python3
"""fclimb.py <m.ll> <singles.jsonl> <out.log> [rounds=20] [topk=60] [base_json] [nproc=6]: forward selection of greedy
override sets (w15a18 climb.py on the light fscr cell; objective = scorer M). Each round re-scores base+c for the top-K
singles (by single M) not yet used and keeps the best if it raises M."""
import sys,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import fscr, multiprocessing as mp
KEYS=('prio','force','hint','casc','weight','nohint')
def comb(a,b):
    r=dict(a)
    for k in KEYS:
        if b.get(k): r[k]=(r[k]+','+b[k]) if r.get(k) else b[k]
    return r
def main():
    m,sf,of=sys.argv[1:4]; rounds=int(sys.argv[4]) if len(sys.argv)>4 else 20; K=int(sys.argv[5]) if len(sys.argv)>5 else 60
    base=json.loads(sys.argv[6]) if len(sys.argv)>6 and sys.argv[6] else {}; npr=int(sys.argv[7]) if len(sys.argv)>7 else 6
    S=[json.loads(l) for l in open(sf)]; S=[s for s in S if 'M' in s]
    for s in S: s.pop('keep',None)
    cur=dict(base); cur['name']=base.get('name','base')
    log=open(of,'a')
    if True:
        best=fscr.prun([(m,cur)],1)[0]; print('start',best.get('M'),best.get('bytes'),flush=True)
        log.write(json.dumps(dict(best,step=-1))+'\n'); log.flush()
        used=set(); cands=sorted(S,key=lambda s:-s['M'])[:K]
        for r in range(rounds):
            jobs=[]
            for c in cands:
                if c['name'] in used: continue
                j=comb({k:cur[k] for k in KEYS if cur.get(k)},c); j['name']=cur['name']+'+'+c['name']; j['add']=c['name']; jobs.append((m,j))
            res=[x for x in fscr.prun(jobs,npr) if 'M' in x]; res.sort(key=lambda x:(-x['M'],abs(x['bytes']-27400)))
            for x in res[:3]: print(f"  r{r} {x['add']:14s} M {x['M']} bytes {x['bytes']}",flush=True)
            if not res or res[0]['M']<=best['M']: print('stop',flush=True); break
            best=res[0]; cur={k:best[k] for k in KEYS if best.get(k)}; cur['name']=best['name']; used.add(best['add'])
            log.write(json.dumps(dict(best,step=r))+'\n'); log.flush()
            print(f"step {r}: +{best['add']} -> M {best['M']} bytes {best['bytes']} ratio {best['ratio']}",flush=True)
    print('FINAL',json.dumps(best),flush=True)
if __name__=='__main__': main()
