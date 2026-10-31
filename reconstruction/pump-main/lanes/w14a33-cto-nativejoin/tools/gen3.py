import json,os,glob
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a33-cto-nativejoin/e/')
SRC=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a33-cto-nativejoin/programs/pump/src/creator/admin_cto.rs').read()
base=json.load(open(O+'r1j1.py'.replace('.py','.py'))) if False else None
g={};exec(open(O+'r1j1.py').read(),g); B=g['EDITS']
s=SRC
for a,b in B: assert s.count(a)==1; s=s.replace(a,b)
K=json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']
names=[]
for k in K:
    if not k.get('edit'): continue
    ed=[[e['old'],e['new']] for e in k['edit']]
    t=s; ok=True
    for a,b in ed:
        if t.count(a)!=1 or a.count('\n')!=b.count('\n'): ok=False;break
        t=t.replace(a,b)
    if not ok: continue
    n='m3k_'+k['name']; open(O+n+'.py','w').write('EDITS='+json.dumps(B+ed)+'\n'); names.append(n)
# w14a31 knob8 genes
for f in sorted(glob.glob(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a31-cto-knob8/e/*.py'))):
    nm=os.path.basename(f)[:-3]
    if nm.startswith('n_') or nm.startswith('base') or nm in ('s_rent_get',): continue
    gg={};
    try: exec(open(f).read(),gg)
    except Exception: continue
    ed=gg.get('EDITS',[]); t=s; ok=bool(ed)
    for e in ed:
        if not isinstance(e,(list,tuple)): ok=False;break
        a,b=e
        if t.count(a)!=1 or a.count('\n')!=b.count('\n'): ok=False;break
        t=t.replace(a,b)
    if not ok: continue
    n='m3q_'+nm; open(O+n+'.py','w').write('EDITS='+json.dumps(B+[list(e) for e in ed])+'\n'); names.append(n)
print(' '.join(names))
