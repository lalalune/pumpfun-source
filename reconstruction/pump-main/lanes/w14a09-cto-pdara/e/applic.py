import sys,json,os
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a09-cto-pdara/g47'))
sys.path.insert(0,os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a09-cto-pdara/e'))
import genes47, gen
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a09-cto-pdara'
src=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
for a,b in gen.G['pda']: assert src.count(a)==1; src=src.replace(a,b)
P={}
for k,v in genes47.G.items():
    if v: P['g_'+k]=v
for k in json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']:
    P['k_'+k['name']]=[(e['old'],e['new']) for e in (k.get('edit') or [])]
ok={}
for k,v in P.items():
    s=src; good=True
    for a,b in v:
        if s.count(a)!=1: good=False;break
        s=s.replace(a,b)
    if good and s.count('\n')==src.count('\n') and s!=src: ok[k]=v
json.dump(ok,open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a09-cto-pdara/e/partners.json'),'w'))
print(len(P),len(ok)); print(' '.join(sorted(ok)))
