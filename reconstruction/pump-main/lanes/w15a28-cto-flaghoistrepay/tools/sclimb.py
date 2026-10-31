#!/usr/bin/env python3
"""sclimb.py <m.ll> <singles.jsonl> <out.jsonl> <base_force> [K] [rounds] [--size N]: greedy climb of sticky forces on a fixed base
force set (RAPRIO_STICKY=1 expected in env). Singles rows: {'name','force':'<base>,<v>=<r>'}; the last force term is the gene."""
import sys,os,json,multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import screen
def job(g,base): return {'name':'+'.join(g) or 'base','force':','.join([x for x in [base]+g if x]),'full':1}
def ok(x,size): return 'ratio' in x and (size is None or x['bytes']==size)
if __name__=='__main__':
    a=sys.argv[1:]; m,sf,of,base=a[:4]; K=int(a[4]) if len(a)>4 else 30; R=int(a[5]) if len(a)>5 else 8
    size=int(a[a.index('--size')+1]) if '--size' in a else None
    S=[json.loads(l) for l in open(sf) if l.strip()]; S=[x for x in S if 'ratio' in x and x['name']!='base']; S.sort(key=lambda x:-x['ratio'])
    genes=[x['force'].split(',')[-1] for x in S[:K]]
    screen.init(m); best=screen.run(job([],base)); cur=[]; print(json.dumps({'round':0,**best}),flush=True); out=open(of,'a')
    with mp.Pool(3,initializer=screen.init,initargs=(m,)) as p:
        for rd in range(1,R+1):
            tr=[g for g in genes if g not in cur]; res=list(p.imap(screen.run,[job(cur+[g],base) for g in tr]))
            for x in res: out.write(json.dumps(x)+'\n')
            c=[(x,g) for x,g in zip(res,tr) if ok(x,size)]
            if not c: break
            x,g=max(c,key=lambda t:t[0]['ratio'])
            if ok(best,size) and x['ratio']<=best['ratio']: print('no improvement',flush=True); break
            cur.append(g); best=x; print(json.dumps({'round':rd,**best}),flush=True)
