#!/usr/bin/env python3
"""dp.py: joint search over single-clone captures (this lane's res-*.jsonl): at most one spelling per literal group
(H a1, T0..T6 to_account_info clones, Q a2, T8, P a3, T10, G a4). Objective = the full abort-jump profile:
pred M = M_main + sum(dM_i) + [good(main cum + sum dcum_i) - good(main) - sum(good(cum_i) - good(main))] (additive model,
each single's dM already counts its own jump changes). Exhaustive over groups (product of options incl. 'none').
Prints the top predictions; the top composites are then priced with splice.py / captured."""
import sys,os,json,glob,itertools
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from prof import rel
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a15-cto-tcfprofile')
MAIN=open(OUT+'/an/main.bin','rb').read(); MC=rel(MAIN)[0]; MM=2251
def good(c): return sum(1 for x in c if x==0)
G0=good(MC)
def group(genes):
    gs=genes.split('+')
    if len(gs)!=1: return None
    g=gs[0]
    if g.startswith(('P:','c2')): return 'P'
    if g[0] in 'HQG' and g[1]==':': return g[0]
    if g[0]=='T': return g.split(':')[0]
    return None
rows=[]
for f in glob.glob(OUT+'/res-*.jsonl'):
    for l in open(f):
        r=json.loads(l)
        if 'error' in r or r['name']=='main': continue
        g=group(r.get('genes',''))
        if not g: continue
        fb=f'{OUT}/rx/{r["name"]}/fn.bin'; raw=open(fb,'rb').read(); c=rel(raw)[0]
        if c is None: continue
        rows.append({'name':r['name'],'g':g,'dM':r['M']-MM,'db':r['bytes']-27400,'dc':[a-b for a,b in zip(c,MC)],'dg':good(c)-G0})
groups={}
for r in rows: groups.setdefault(r['g'],[]).append(r)
keys=sorted(groups)
opts=[[None]+groups[k] for k in keys]
best=[]
n=1
for o in opts: n*=len(o)
print('groups',{k:len(groups[k]) for k in keys},'combos',n,file=sys.stderr)
for combo in itertools.product(*opts):
    sel=[x for x in combo if x]
    if not sel: continue
    cum=[MC[j]+sum(x['dc'][j] for x in sel) for j in range(41)]
    inter=good(cum)-G0-sum(x['dg'] for x in sel)
    pM=MM+sum(x['dM'] for x in sel)+inter; db=sum(x['db'] for x in sel)
    best.append((pM,db,good(cum),sum(1 for x in cum[:25] if x==0),[x['name'] for x in sel]))
best.sort(key=lambda x:(-x[0]))
for b in best[:int(sys.argv[1]) if len(sys.argv)>1 else 30]: print(b)
print('--- best by abort good (TCF good >= 13):')
for b in sorted([b for b in best if b[3]>=13],key=lambda x:(-x[3],-x[0]))[:15]: print(b)
