#!/usr/bin/env python3
"""gen3.py: tai base x every applicable size knob (sizeknobs-cto.json + w14a73 cat_apply.json). Writes e/k_<name>.py."""
import json,runpy,re
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a26-cto-taiupstream'
E='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a26-cto-taiupstream/e'
s=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
T=runpy.run_path(E+'/p_tai.py')['EDITS']
t=s
for a,b in T: t=t.replace(a,b)
K={}
for k in json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']:
    if k.get('edit'): K[k['name']]=[(e['old'],e['new']) for e in k['edit']]
for kind,name,ed in json.load(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a73-cto-autospell/cat_apply.json')):
    K.setdefault(name,[tuple(x) for x in ed])
out=[];seen=set()
for n,ed in K.items():
    if not all(t.count(a)==1 and a.count('\n')==b.count('\n') for a,b in ed): continue
    if any('read_volatile' in b or 'black_box' in b for a,b in ed): continue
    key=repr(ed)
    if key in seen: continue
    seen.add(key)
    nm='k_'+re.sub(r'\W','_',n)
    open(f'{E}/{nm}.py','w').write('EDITS='+repr(list(T)+ed)+'\n'); out.append(nm)
print(' '.join(out))
