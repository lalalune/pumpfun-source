#!/usr/bin/env python3
"""greedyp.py <base.ll> <edits.jsonl> <singles.jsonl[,more]> <out.jsonl> <start ids,comma|-> [workers] [rounds] [--M0 n] [--base-sig s]
Greedy forward selection (process pool). Each round tries cur+[c] and cur+[c,r] for repay cells r (single dB = -(dB of c'))
so off-size improvers can enter with a size repay. Accept the best M at exactly 27,400 B if it beats the current."""
import sys,os,json,hashlib
import multiprocessing as mp
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
def main():
    A=sys.argv[1:]
    def opt(k,d=None): return A[A.index(k)+1] if k in A else d
    base,ef,sfs,outf,start=A[0:5]
    W=int(A[5]) if len(A)>5 and not A[5].startswith('--') else 6
    RN=int(A[6]) if len(A)>6 and not A[6].startswith('--') else 4
    M0=int(opt('--M0','2287')); BSIG=opt('--base-sig','85d273bcd66a')
    sys.argv=[sys.argv[0],base,ef,'/dev/null']  # screenp argv contract
    import screenp
    screenp.init(base,ef)
    S=[]
    for sf in sfs.split(','):
        S+=[json.loads(l) for l in open(sf)]
    S=[r for r in S if 'M' in r and '+' not in r['id'] and r['sig']!=BSIG]
    best_single={}
    for r in S: best_single[r['id']]=r
    cand=[i for i,r in best_single.items() if r['M']-M0>=int(opt('--minD','-3')) and abs(r['bytes']-27400)<=int(opt('--maxB','24'))]
    # dedupe by sig: keep one representative per output signature
    seen={}; 
    for i in sorted(cand,key=lambda i:(-best_single[i]['M'],i)):
        s=best_single[i]['sig']
        if s not in seen: seen[s]=i
    cand=list(seen.values())
    cur=[] if start=='-' else start.split(',')
    cache={}
    if os.path.exists(outf):
        for l in open(outf):
            r=json.loads(l); cache[r['id']]=r
    def key(ids): return '+'.join(sorted(ids))
    def ev_many(sets):
        todo=[s for s in sets if key(s) not in cache]
        if todo:
            with mp.Pool(W,initializer=screenp.init,initargs=(base,ef)) as p:
                for s,r in zip(todo,p.map(screenp.run1,[sorted(s) for s in todo],chunksize=1)):
                    r['id']=key(s); cache[key(s)]=r
                    with open(outf,'a') as f: f.write(json.dumps(r)+'\n')
        return [cache[key(s)] for s in sets]
    cur_r=ev_many([cur])[0] if cur else {'M':M0,'bytes':27400}
    print('start',cur,cur_r.get('M'),cur_r.get('bytes'),'cands',len(cand),flush=True)
    def lines(i): return set(int(k) for k in screenp.E[i]['rep'])
    for rnd in range(RN):
        used=set().union(*[lines(i) for i in cur]) if cur else set()
        cs=[c for c in cand if c not in cur and not (lines(c)&used)]
        trials=[cur+[c] for c in cs]
        res=ev_many(trials)
        ok=[(t,r) for t,r in zip(trials,res) if 'M' in r]
        at=[(t,r) for t,r in ok if r['bytes']==27400]
        # repay pairs for the top off-size trials
        off=sorted([(t,r) for t,r in ok if r['bytes']!=27400 and r['M']>=cur_r['M']],key=lambda x:-x[1]['M'])[:int(opt('--offN','12'))]
        pairs=[]
        for t,r in off:
            need=27400-r['bytes']
            reps=[c for c in cs if c not in t and best_single[c]['bytes']-27400==need and not (lines(c)&set().union(*[lines(i) for i in t]))]
            reps=sorted(reps,key=lambda c:-best_single[c]['M'])[:int(opt('--repN','8'))]
            pairs+=[t+[c] for c in reps]
        if pairs:
            pres=ev_many(pairs)
            at+=[(t,r) for t,r in zip(pairs,pres) if 'M' in r and r['bytes']==27400]
        if not at: print('round',rnd,'no 27400 trial'); break
        t,r=max(at,key=lambda x:x[1]['M'])
        print('round',rnd,'best',t,r['M'],r['bytes'],flush=True)
        if r['M']<=cur_r['M']: break
        cur=t; cur_r=r
    print('final',cur,cur_r,flush=True)

if __name__=='__main__':
    mp.set_start_method('fork')
    main()
