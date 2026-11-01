#!/usr/bin/env python3
"""hc.py <log.jsonl> <rounds> <batch> <workers> [start-spec]: batch hill-climb over pre-opt validate weights + block moves (fx oracle).
spec = 'W1:p,W2:p|A>B;C>D'. Accept strictly better M at 27400 B; sideways (equal M, new sig) allowed once per sig."""
import sys,os,json,random,shutil
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import vx,fx,pmv
OUT=os.path.dirname(T)
base=open(os.environ.get('VXBASE',OUT+'/cap_m1/slim.ll')).read()
NAMES=pmv.names(base)
BR=list(vx.BR.keys())
P=[0.1,0.2,0.3,0.375,0.45,0.5,0.55,0.625,0.7,0.8,0.9]
MOV=['bb2','bb10','bb17','bb80','bb27','bb32','bb40','bb49','bb54','bb59','bb67','bb23','bb22','bb14','bb7','bb16','bb28','bb37','bb39','bb96','bb48','bb53','bb55','bb63','bb64','bb45','bb46','bb79','bb9','bb71']
def parse(s):
    w,_,m=s.partition('|')
    W=dict(x.split(':') for x in w.split(',') if x); M=[x for x in m.split(';') if x]
    return W,M
def fmt(W,M): return ','.join('%s:%s'%(k,v) for k,v in W.items())+'|'+';'.join(M)
def nb(s):
    W,M=parse(s); W=dict(W); M=list(M)
    r=random.random()
    if r<0.45:
        b=random.choice(BR); W[b]=str(random.choice(P))
    elif r<0.85:
        a=random.choice(MOV); y=random.choice(NAMES[1:])
        if a!=y: M.append('%s>%s'%(a,y))
    else:
        if M and (not W or random.random()<0.5): M.pop(random.randrange(len(M)))
        elif W: W.pop(random.choice(list(W)))
    return fmt(W,M)
k=[0]
def ev(s):
    k[0]+=1; name='hc_%d_%d'%(os.getpid(),k[0])
    W,M=parse(s)
    try:
        t=vx.edit(base,','.join('%s:%s'%(a,b) for a,b in W.items()))
        if M: t=pmv.move(t,';'.join(M))
    except Exception as e: return {'spec':s,'err':str(e)[:100]}
    r=fx.run(t,name); shutil.rmtree(OUT+'/fx/'+name,ignore_errors=True); r['spec']=s; return r
if __name__=='__main__':
    logp,rounds,batch,nw=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])
    cur=sys.argv[5] if len(sys.argv)>5 else '|'
    random.seed(int(os.environ.get('SEED','1')))
    r0=ev(cur); best=r0.get('M',0); seen={r0.get('sig')}
    lg=open(logp,'a'); lg.write(json.dumps({'start':cur,'M':best})+'\n'); lg.flush()
    with ThreadPoolExecutor(nw) as ex:
        for rd in range(rounds):
            cands=list({nb(cur) for _ in range(batch)})
            res=list(ex.map(ev,cands))
            for r in res: lg.write(json.dumps(r)+'\n')
            ok=[r for r in res if r.get('bytes')==27400 and 'M' in r]
            ok.sort(key=lambda r:-r['M'])
            moved=False
            for r in ok:
                if r['M']>best or (r['M']==best and r['sig'] not in seen):
                    cur=r['spec']; moved=r['M']>best; best=max(best,r['M']); seen.add(r['sig']); break
            lg.write(json.dumps({'round':rd,'best':best,'cur':cur})+'\n'); lg.flush()
