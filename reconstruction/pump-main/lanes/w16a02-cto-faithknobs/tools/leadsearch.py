#!/usr/bin/env python3
"""leadsearch.py <catalog.json> <lead fn.bin> <out.jsonl> [NP] [--pairs]: splice-oracle screen of lead + one catalogued
capture (and with --pairs lead + two) so that the total is 27,400 B. Experiment only."""
import sys,os,json,itertools
from multiprocessing import Pool
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import splice
cat=json.load(open(sys.argv[1])); LEAD=sys.argv[2]; OUTF=sys.argv[3]
NP=int(sys.argv[4]) if len(sys.argv)>4 and sys.argv[4].isdigit() else 6
PAIRS='--pairs' in sys.argv
C=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes')
def fbpath(d): return f"{C}/{d['lane']}/rx/{d['name']}/fn.bin"
MAIN=open(C+'/w16a02-cto-faithknobs/rx/main/fn.bin','rb').read()
B=splice.parse(MAIN); BT=splice.targets(B)
L=open(LEAD,'rb').read(); LV=splice.Var(B,L); need=27400-len(L)
items=[d for d in cat if d['M']>=2200 and not d['identical_to_main'] and os.path.exists(fbpath(d))]
V=[splice.Var(B,open(fbpath(d),'rb').read()) for d in items]
combos=[(i,) for i in range(len(items)) if items[i]['delta_bytes']==need]
if PAIRS:
    for i,j in itertools.combinations(range(len(items)),2):
        if items[i]['delta_bytes']+items[j]['delta_bytes']==need: combos.append((i,j))
def ev(c):
    s=splice.splice(MAIN,[LV]+[V[i] for i in c],B,BT)
    if s is None: return None
    return (c,len(s),splice.M(s))
if __name__=='__main__':
    print(len(items),'items',len(combos),'combos need',need,flush=True)
    with Pool(NP) as P, open(OUTF,'w') as f:
        for r in P.imap_unordered(ev,combos,chunksize=4):
            if r is None: continue
            c,b,m=r
            f.write(json.dumps({'lead':os.path.basename(os.path.dirname(LEAD)),'names':[items[i]['name'] for i in c],'lanes':[items[i]['lane'] for i in c],
                                'genes':[items[i]['genes'] for i in c],'deltas':[items[i]['delta_bytes'] for i in c],'bytes':b,'M':m})+'\n')
            if m>=2248: print('HIT',m,[items[i]['name'] for i in c],flush=True)
    print('done',flush=True)
