#!/usr/bin/env python3
"""genknob.py <base_edits.py> <outdir> <prefix>: one variant per size knob (w13a34 knobs13 K + w11 sizeknobs-cto.json) on top of base edits,
kept only if every knob old string occurs exactly once in the base-edited admin_cto.rs and newline counts hold."""
import sys,os,json
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a27-cto-hvatalit'
src=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
base,d,pre=sys.argv[1:4]; os.makedirs(d,exist_ok=True)
g={}; exec(open(base).read(),g); BE=g['EDITS']
s=src
for a,b in BE: assert s.count(a)==1; s=s.replace(a,b)
K={}
g2={}; exec(open(os.path.join(os.path.dirname(__file__),'knobs13.py')).read(),g2)
for n,e in g2['K'].items(): K['n_'+n]=[tuple(x) for x in e]
cat=json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))
for k in cat['knobs']:
    if k.get('edit'): K['w_'+k['name']]=[(x['old'],x['new']) for x in k['edit']]
ok=[]
for n,e in K.items():
    t=s; good=True
    for a,b in e:
        if t.count(a)!=1 or a.count('\n')!=b.count('\n'): good=False; break
        t=t.replace(a,b)
    if not good or t==s: continue
    open(f'{d}/{pre}{n}.py','w').write('EDITS=%r\n'%(BE+e,)); ok.append(pre+n)
print('\n'.join(ok))
