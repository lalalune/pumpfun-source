#!/usr/bin/env python3
"""pairsearch.py <catalog.json> <out.jsonl> [NP] [--triples]: splice-oracle screen of every conflict-free pair (and,
with --triples, triple) of catalogued captures whose byte deltas sum to 0 (27,400 B). Prints/records the predicted M.
The splice oracle reproduced 43/54 cached pair builds byte for byte and 52/54 in M (see NOTES). Experiment only."""
import sys,os,json,itertools
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import splice
cat=json.load(open(sys.argv[1])); OUTF=sys.argv[2]; NP=int(sys.argv[3]) if len(sys.argv)>3 and sys.argv[3].isdigit() else 6
TRI='--triples' in sys.argv
C=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes')
def fbpath(d): return f"{C}/{d['lane']}/rx/{d['name']}/fn.bin"
MAIN=open(C+'/w16a02-cto-faithknobs/rx/main/fn.bin','rb').read()
B=splice.parse(MAIN); BT=splice.targets(B)
items=[d for d in cat if d['M']>=2200 and not d['identical_to_main'] and os.path.exists(fbpath(d))]
V={}
def var(i):
    if i not in V: V[i]=splice.Var(B,open(fbpath(items[i]),'rb').read())
    return V[i]
for i in range(len(items)): var(i)
combos=[]
n=len(items)
for i,j in itertools.combinations(range(n),2):
    if os.environ.get('NOPAIRS')!='1' and items[i]['delta_bytes']+items[j]['delta_bytes']==0 and not (items[i]['delta_bytes']==0): combos.append((i,j))
if TRI:
    big=[i for i in range(n) if 8<=abs(items[i]['delta_bytes'])<=128 and items[i]['dM']>=int(os.environ.get('TRI_MIN_DM','-8'))]
    for i,j,k in itertools.combinations(big,3):
        if items[i]['delta_bytes']+items[j]['delta_bytes']+items[k]['delta_bytes']==0: combos.append((i,j,k))
def ev(c):
    s=splice.splice(MAIN,[V[i] for i in c],B,BT)
    if s is None: return None
    return (c,len(s),splice.M(s))
if __name__=='__main__':
    print(len(items),'items',len(combos),'combos',flush=True)
    with Pool(NP) as P, open(OUTF,'w') as f:
        for r in P.imap_unordered(ev,combos,chunksize=8):
            if r is None: continue
            c,b,m=r
            f.write(json.dumps({'names':[items[i]['name'] for i in c],'lanes':[items[i]['lane'] for i in c],'genes':[items[i]['genes'] for i in c],
                                'deltas':[items[i]['delta_bytes'] for i in c],'Ms':[items[i]['M'] for i in c],'bytes':b,'M':m})+'\n')
            if m>=2249: print('HIT',m,[items[i]['name'] for i in c],flush=True)
    print('done',flush=True)
