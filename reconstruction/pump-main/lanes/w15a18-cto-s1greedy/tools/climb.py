#!/usr/bin/env python3
"""climb.py <m.ll> <singles.jsonl> <out.log> <objective M|pinV|pinA> [rounds] [topk] [base_json]: forward selection of override sets."""
import sys,os,json,subprocess,tempfile
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scr, multiprocessing as mp
def main():
    m,sf,of,obj=sys.argv[1:5]; rounds=int(sys.argv[5]) if len(sys.argv)>5 else 8; K=int(sys.argv[6]) if len(sys.argv)>6 else 60
    base=json.loads(sys.argv[7]) if len(sys.argv)>7 else {}
    KEYS=('prio','force','hint','casc','weight','nohint')
    S=[json.loads(l) for l in open(sf)]; S=[s for s in S if obj in s and s[obj] is not None]
    def comb(a,b):
        r=dict(a)
        for k in KEYS:
            if b.get(k): r[k]=(r[k]+','+b[k]) if r.get(k) else b[k]
        return r
    os.makedirs(scr.O+'/tmp',exist_ok=True)
    cur=dict(base); cur['name']='base'
    with mp.Pool(6) as p:
        best=p.map(scr.run,[(m,cur)])[0]; print('start',best.get('M'),best.get('pinV'),best.get('pinA'),best.get('bytes'),flush=True)
        used=set()
        cands=sorted(S,key=lambda s:-s[obj])[:K]
        log=open(of,'a')
        for r in range(rounds):
            jobs=[]
            for c in cands:
                if c['name'] in used: continue
                j=comb(cur,c); j['name']=cur.get('name','')+'+'+c['name']; j['add']=c['name']; jobs.append((m,j))
            res=[x for x in p.map(scr.run,jobs) if obj in x and x[obj] is not None]
            res.sort(key=lambda x:-x[obj])
            for x in res[:3]: print(f"  r{r} {x['add']:14s} M {x.get('M')} pinV {x.get('pinV')} pinA {x.get('pinA')} bytes {x.get('bytes')}",flush=True)
            if not res or res[0][obj]<=best[obj]: print('stop'); break
            best=res[0]; cur={k:best[k] for k in KEYS if best.get(k)}; cur['name']=best['name']; used.add(best['add'])
            log.write(json.dumps(best)+'\n'); log.flush()
            print(f"step {r}: {best['name']} -> M {best.get('M')} pinV {best.get('pinV')} pinA {best.get('pinA')} bytes {best.get('bytes')}",flush=True)
    print('FINAL',json.dumps(best))
    
if __name__=='__main__': main()
