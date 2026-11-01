#!/usr/bin/env python3
"""drift.py: neutral-drift harvest helpers (experiment only, w17a33-shim-drift).
  drift.py ref                                   -> res/ref.json  (main reference: id -> [dM,dB,sig] from all tables)
  drift.py mkb <name> <A ids comma> [--local N] [--all]  -> b/<name>.combo (one combo per line: A... B)
  drift.py ana <name> <base_sig>                 -> summary of b/<name>.jsonl
  drift.py pairs <name> <base_sig> [--k K]       -> b/<name>_p.combo (size-complementary pairs on the base)
"""
import sys,os,json,re,collections
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MS='61dcfe87f489'; MM=2295; SZ=27400
def U():
    d={}
    for l in open(OUT+'/gen/U.jsonl'):
        e=json.loads(l); d[e['id']]=e
    return d
def lines(e): return sorted(int(k) for k in e['rep'])
def famrank(e):
    k=e['id'].split(':')[0]
    order=['pt','pb','ai','ap','ax','vl','vs','bwt','bwf','sw0','sw1','sw2','rr','rrc','bf','na','nar','vaA','vaB','vaC','eqn','eqa','eqf','rg1','rg2','au','se']
    return order.index(k) if k in order else 50
def ref():
    R={}
    rows=json.load(open(OUT+'/res/main_tables.json'))
    def norm(k):
        if k.startswith('va') and '_' in k and ':' not in k:
            a,fn,nm=k.split('_',2); return f'{a}:{fn}:%{nm}'
        return k
    for k,v in rows.items(): R[norm(k)]=[v[1],v[2],v[3]]
    for f in ['g_main.jsonl','verify_neu.jsonl']:
        p=OUT+'/res/'+f
        if not os.path.exists(p): continue
        for l in open(p):
            r=json.loads(l)
            if 'M' in r: R[r['id']]=[r['M']-MM,r['bytes']-SZ,r['sig']]
    json.dump(R,open(OUT+'/res/ref.json','w'))
    return R
def loadref():
    return json.load(open(OUT+'/res/ref.json'))
def bsig(R,E,dm0=-30,dmoff=-6,boff=16):
    """one representative per main signature of code-changing cells near size; va cells without sig kept individually"""
    groups=collections.defaultdict(list)
    for k,(dm,db,sig) in R.items():
        if k not in E or sig==MS: continue
        if (db==0 and dm>=dm0) or (db!=0 and abs(db)<=boff and dm>=dmoff):
            groups[sig or ('nosig:'+k)].append(k)
    reps=[]
    for s,ks in groups.items():
        ks.sort(key=lambda k:(famrank(E[k]),k)); reps.append(ks[0])
    return reps
def blocal(E,A,n):
    out=[]
    al={(E[a]['fn'] if 'fn' in E[a] else None, x) for a in A for x in lines(E[a])}
    afn={E[a].get('fn') for a in A}
    alines=[x for a in A for x in lines(E[a])]
    for k,e in E.items():
        if k in A or e.get('fn') not in afn: continue
        if e['id'].split(':')[0]=='bp': continue
        ls=lines(e)
        if any(abs(x-y)<=n for x in ls for y in alines): out.append(k)
    return out
def mkb(name,A,local=40,allb=False):
    E=U(); R=loadref()
    B=set(bsig(R,E))
    if local: B|=set(blocal(E,A,local))
    if allb: B|=set(k for k in E if k.split(':')[0]!='bp')
    Al=set(x for a in A for x in lines(E[a]))
    B=[b for b in B if b not in A and not (set(lines(E[b]))&Al)]
    B.sort(key=lambda b:(famrank(E[b]),b))
    os.makedirs(OUT+'/b',exist_ok=True)
    with open(OUT+f'/b/{name}.combo','w') as f:
        for b in B: f.write(' '.join(A+[b])+'\n')
    return len(B)
def ana(name,bs,show=12):
    res=[json.loads(l) for l in open(OUT+f'/b/{name}.jsonl')]
    c=collections.Counter(); above=[]; neu=[]; off=[]
    for r in res:
        if 'M' not in r: c['err']+=1; continue
        if r['sig'] in (bs,): c['same-as-base']+=1; continue
        if r['sig']==MS: c['main']+=1; continue
        if r['bytes']==SZ:
            if r['M']>MM: above.append(r)
            elif r['M']==MM: neu.append(r)
            else: c['0B below']+=1
        else: off.append(r)
    print(name,len(res),dict(c),'above',len(above),'neutral',len(neu),'off',len(off))
    for r in sorted(above,key=lambda r:-r['M'])[:show]: print('  ABOVE',r['id'],r['M'],r['bytes'],r['sig'])
    offs=sorted(off,key=lambda r:-r['M'])[:show]
    for r in offs: print('  off',r['id'].split('+')[-1],r['M'],r['bytes'])
    return above,neu,off
if __name__=='__main__':
    a=sys.argv[1:]
    if a[0]=='ref': R=ref(); print(len(R))
    elif a[0]=='mkb':
        n=a[1]; A=a[2].split(','); loc=int(a[a.index('--local')+1]) if '--local' in a else 40
        print(mkb(n,A,loc,'--all' in a))
    elif a[0]=='ana': ana(a[1],a[2])
def mkk(name,A,dbt=8,thr=-20,local=15):
    """knob base: A (size knob at -dbt) x every +dbt cell (dM>=thr) + B_sig + B_local"""
    E=U(); R=loadref()
    B=set(k for k,v in R.items() if k in E and v[2]!=MS and v[1]==dbt and v[0]>=thr)
    B|=set(bsig(R,E))
    if local: B|=set(blocal(E,A,local))
    Al=set(x for a in A for x in lines(E[a]))
    B=[b for b in B if b not in A and not (set(lines(E[b]))&Al) and not b.startswith('kn:')]
    B.sort(key=lambda b:(-(R.get(b,[0,0])[1]==dbt),famrank(E[b]),b))
    with open(OUT+f'/b/{name}.combo','w') as f:
        for b in B: f.write(' '.join(A+[b])+'\n')
    return len(B)
if __name__=='__main__' and sys.argv[1]=='mkk':
    print(mkk(sys.argv[2],sys.argv[3].split(','),int(sys.argv[4]) if len(sys.argv)>4 else 8))
