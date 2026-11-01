#!/usr/bin/env python3
"""newscan.py <catalog.json> <name>... : for each new capture rx/<name>/fn.bin of this lane, splice it with every catalogued
capture or zero-sum pair of captures so that the composite is 27,400 B, and print the best predicted M. Captures whose
genes contain devol or tf_g3/O bases (w15a29, w15a25) are skipped as partners. Experiment only."""
import sys,os,json,itertools
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import splice
C=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes')
cat=json.load(open(sys.argv[1]))
def fbpath(d): return f"{C}/{d['lane']}/rx/{d['name']}/fn.bin"
MAIN=open(C+'/w16a02-cto-faithknobs/rx/main/fn.bin','rb').read()
B=splice.parse(MAIN); BT=splice.targets(B)
bad=lambda g: any(x in (g or '') for x in ('devol','tf_g3','O+','O_'))
items=[d for d in cat if d['M']>=2236 and not d['identical_to_main'] and not bad(d['genes']) and abs(d['delta_bytes'])<=200 and os.path.exists(fbpath(d))]
V=[splice.Var(B,open(fbpath(d),'rb').read()) for d in items]
def ev(a):
    LV,c=a
    s=splice.splice(MAIN,[LV]+[V[i] for i in c],B,BT)
    return None if s is None else (c,len(s),splice.M(s))
if __name__=='__main__':
    print(len(items),'partner items',flush=True)
    for name in sys.argv[2:]:
        fb=f'{C}/w16a02-cto-faithknobs/rx/{name}/fn.bin'
        if not os.path.exists(fb): print(name,'missing'); continue
        raw=open(fb,'rb').read(); need=27400-len(raw); LV=splice.Var(B,raw)
        combos=[(i,) for i in range(len(items)) if items[i]['delta_bytes']==need]
        combos+=[(i,j) for i,j in itertools.combinations(range(len(items)),2) if items[i]['delta_bytes']+items[j]['delta_bytes']==need and items[i]['delta_bytes']!=0]
        if need==0: combos.append(())
        with Pool(int(os.environ.get('NP','3'))) as P: res=[r for r in P.map(ev,[(LV,c) for c in combos],chunksize=4) if r]
        res.sort(key=lambda r:-r[2])
        with open(f'{C}/w16a02-cto-faithknobs/new_{name}.jsonl','w') as f:
            for c,b,m in res: f.write(json.dumps({'lead':name,'names':[items[i]['name'] for i in c],'lanes':[items[i]['lane'] for i in c],'genes':[items[i]['genes'] for i in c],'bytes':b,'M':m})+'\n')
        print(name,len(raw),'need',need,'combos',len(combos),'ok',len(res),'best',[(m,[items[i]['name'] for i in c]) for c,b,m in res[:3]],flush=True)
