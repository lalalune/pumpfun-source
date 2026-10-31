# gene pool: g.* (genes47) and K.* (sizeknobs) + skelunion genes; applied AFTER base edits (v7c) on the resulting text
import sys,os,json,runpy
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a47-cto-stitch9/tools'))
P={}
try:
    import genes47 as g47
    for k,v in g47.G.items():
        if v and not callable(v): P['g.'+k]=v
except Exception as e: print('g47 fail',e,file=sys.stderr)
for k in json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']:
    if k.get('edit'): P.setdefault('K.'+k['name'],[(e['old'],e['new']) for e in k['edit']])

import glob as _g
for _f in sorted(_g.glob(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a31-cto-knob8/e/*.py'))):
    _n=os.path.basename(_f)[:-3]
    if _n.startswith(('gen','base','combo','mkv7c','v7c')): continue
    try:
        _E=runpy.run_path(_f).get('EDITS')
        if _E and not any(callable(x) for x in _E): P['k8.'+_n]=[tuple(x) for x in _E]
    except Exception: pass
def apply(s,E):
    n0=s.count('\n')
    for a,b in E:
        if s.count(a)!=1: return None
        s=s.replace(a,b)
    return s if s.count('\n')==n0 else None
try:
    _s11=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'s11genes.py'))['G']
    for _k,_v in _s11.items():
        if isinstance(_v,list) and _v and all(isinstance(x,tuple) and len(x)==2 for x in _v): P.setdefault('s.'+_k,list(_v))
except Exception as _e: print('s11 fail',_e,file=sys.stderr)
