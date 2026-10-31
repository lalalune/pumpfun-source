#!/usr/bin/env python3
"""climb.py <m.ll> <singles.jsonl> <out.jsonl> [K] [rounds] [--obj ratio|L1|L2] [--size N]: greedy forward selection over the
top-K single RAPRIO overrides (prio/force) of a screen; each round tries adding every remaining candidate to the current
set and keeps the best if it improves the objective (ties broken by ratio). --size N restricts acceptance to N-byte results.
Experiment only."""
import sys,os,json,multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import screen
OBJ=['ratio']
def key(x): return (x.get(OBJ[0],0),x['ratio'])
def merge(sel):
    j={'prio':[], 'force':[], 'hint':[]}
    for c in sel:
        for k in j:
            if c.get(k): j[k].append(c[k])
    r={k:','.join(v) for k,v in j.items() if v}; r['full']=1; r['name']='+'.join(c['name'] for c in sel); return r
if __name__=='__main__':
    a=sys.argv[1:]; m,sf,of=a[:3]; rest=a[3:]
    K=int(rest[0]) if rest and not rest[0].startswith('--') else 120
    R=int(rest[1]) if len(rest)>1 and not rest[1].startswith('--') else 8
    size=None
    if '--obj' in rest: OBJ[0]=rest[rest.index('--obj')+1]
    if '--size' in rest: size=int(rest[rest.index('--size')+1])
    S=[json.loads(l) for l in open(sf) if l.strip()]; S=[x for x in S if 'ratio' in x and not x['eq_main']]
    S.sort(key=lambda x:-x['ratio']); cand=S[:K]
    screen.init(m)
    cur=[]; best=screen.run(merge([])); print(json.dumps({'round':0,**best}),flush=True)
    out=open(of,'a')
    with mp.Pool(int(os.environ.get('CLIMB_N','3')),initializer=screen.init,initargs=(m,)) as p:
        for rd in range(1,R+1):
            used={c['v'] for c in cur}
            trial=[c for c in cand if c['v'] not in used]
            res=list(p.imap(screen.run,[merge(cur+[c]) for c in trial]))
            for x in res: out.write(json.dumps(x)+'\n')
            out.flush()
            ok=[(x,c) for x,c in zip(res,trial) if 'ratio' in x and (size is None or x['bytes']==size)]
            if not ok: break
            x,c=max(ok,key=lambda t:key(t[0]))
            if key(x)<=key(best): print('no improvement',flush=True); break
            cur.append(c); best=x; print(json.dumps({'round':rd,**best}),flush=True)
