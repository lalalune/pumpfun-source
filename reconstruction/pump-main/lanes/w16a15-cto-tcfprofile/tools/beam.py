#!/usr/bin/env python3
"""beam.py [width]: joint search over single-clone captures, one spelling per literal group, objective = the full 41-jump
abort profile. Additive model: pred M = M_main + sum(w_i) + good(cum_main + sum dcum_i) - good(main), where
w_i = dM_i - (good_i - good_main) is the single's non-jump M change. Beam search over groups (exact for the model)."""
import sys,os,json,glob
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from prof import rel
EXCL={'hOKLD','hOKld','hokLD','pKDOL','pKdOL','pKDoL','gKOld','gkoLD','qLkD','qlkd','qLKd','qlKD'}  # case-insensitive rx/ collisions (macOS): superseded by x01..x13
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
    if g.startswith('b'): return g.split(':')[0]
    return None
rows=[]
for f in glob.glob(OUT+'/res-*.jsonl'):
    for l in open(f):
        r=json.loads(l)
        if r['name'] in EXCL: continue
        if 'error' in r or r['name']=='main': continue
        g=group(r.get('genes',''))
        if not g: continue
        raw=open(f'{OUT}/rx/{r["name"]}/fn.bin','rb').read(); c=rel(raw)[0]
        if c is None or r.get('eq_main'): continue
        dc=[a-b for a,b in zip(c,MC)]
        rows.append({'name':r['name'],'genes':r['genes'],'g':g,'dM':r['M']-MM,'db':r['bytes']-27400,'dc':dc,'w':(r['M']-MM)-(good(c)-G0)})
groups={}
for r in rows: groups.setdefault(r['g'],[]).append(r)
W=int(sys.argv[1]) if len(sys.argv)>1 else 3000
beam=[(0,tuple([0]*41),(),0)]   # (sum w, dcum, names, bytes)
for k in sorted(groups):
    nb=list(beam)
    for (sw,dc,names,db) in beam:
        for r in groups[k]:
            nb.append((sw+r['w'],tuple(a+b for a,b in zip(dc,r['dc'])),names+(r['name'],),db+r['db']))
    def score(x): return x[0]+good([a+b for a,b in zip(MC,x[1])])
    nb.sort(key=lambda x:-score(x)); 
    # keep diversity: best per abort-good level too
    keep=nb[:W]; seen=set(id(x) for x in keep); lv={}
    for x in nb:
        g=good([a+b for a,b in zip(MC,x[1])])
        if g not in lv: lv[g]=x
    for x in lv.values():
        if id(x) not in seen: keep.append(x)
    beam=keep
res=[]
for sw,dc,names,db in beam:
    cum=[a+b for a,b in zip(MC,dc)]; g=good(cum)
    res.append({'predM':MM+sw+g-G0,'bytes':27400+db,'good':g,'gt':sum(1 for x in cum[:25] if x==0),'set':list(names)})
res.sort(key=lambda r:-r['predM'])
print('groups',{k:len(v) for k,v in groups.items()})
print('top predicted:')
for r in res[:15]: print(' ',r)
lv={}
for r in res:
    if r['good'] not in lv or r['predM']>lv[r['good']]['predM']: lv[r['good']]=r
print('best predicted M per abort-good level (main 11 of 41):')
for g in sorted(lv): print(' ',g,lv[g])
json.dump({'rows':[{k:v for k,v in r.items() if k!='dc'} for r in rows],'top':res[:200],'levels':lv},open(OUT+'/an/beam.json','w'))
