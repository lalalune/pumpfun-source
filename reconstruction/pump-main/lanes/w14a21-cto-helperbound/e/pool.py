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
def apply(s,E):
    n0=s.count('\n')
    for a,b in E:
        if s.count(a)!=1: return None
        s=s.replace(a,b)
    return s if s.count('\n')==n0 else None
