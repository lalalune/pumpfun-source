#!/usr/bin/env python3
"""collect.py <base_edits.py> <outdir> <prefix> : write one variant per knob from all catalogs, on top of base edits.
Each variant = base edits + one minimal unique (old,new) region edit. Dedupes by resulting text."""
import sys,os,json,glob,runpy
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a50-cto-frozenrepay')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a50-cto-frozenrepay'
src=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
base,d,pre=sys.argv[1:4]; os.makedirs(d,exist_ok=True)
BE=[tuple(x) for x in runpy.run_path(base)['EDITS']]
s=src
for a,b in BE: assert s.count(a)==1,a[:80]; s=s.replace(a,b)
K={}
def add(n,e):
    if n in K: n=n+'_'
    K[n]=e
g=runpy.run_path(O+'/tools/knobs13.py')
for n,e in g['K'].items(): add('n_'+n,list(e))
g=runpy.run_path(O+'/tools/newknobs.py') if os.path.exists(O+'/tools/newknobs.py') else {'K':{}}
for n,e in g['K'].items(): add('t_'+n,list(e))
cat=json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))
for k in cat['knobs']:
    if k.get('edit'): add('w_'+k['name'],[(x['old'],x['new']) for x in k['edit']])
for f in sorted(glob.glob(O+'/k31/*.py')):
    n=os.path.basename(f)[:-3]
    if n.startswith('gen') or n in('combo','mkv7c'): continue
    try: add('a31_'+n,runpy.run_path(f)['EDITS'])
    except Exception as ex: pass
try:
    g=runpy.run_path(O+'/k26/genes.py')
    for n,e in g['G'].items(): add('g26_'+n,e)
except Exception as ex: print('#genes26 fail',ex,file=sys.stderr)
for f in sorted(glob.glob(O+'/k32/*.py')):
    g=runpy.run_path(f)
    if 'EDITS' in g: add('s32_'+os.path.basename(f)[:-3],g['EDITS'])
for f in sorted(glob.glob(O+'/kx/*.py')):
    add('x_'+os.path.basename(f)[:-3],runpy.run_path(f)['EDITS'])
def apply(t,e):
    for x in e:
        if callable(x): t=x(t); continue
        a,b=x
        if t.count(a)!=1 or a.count('\n')!=b.count('\n'): return None
        t=t.replace(a,b)
    return t
def region(s,t):
    i=0
    while s[i]==t[i]: i+=1
    j=0
    while j<len(s)-i and j<len(t)-i and s[-1-j]==t[-1-j]: j+=1
    lo,hi=i,len(s)-j
    while True:
        a=s[lo:hi]
        if a and s.count(a)==1: break
        lo=max(0,lo-8); hi=min(len(s),hi+8)
    return (s[lo:hi],t[lo:len(t)-(len(s)-hi)])
seen={}; ok=[]
for n,e in K.items():
    try: t=apply(s,e)
    except Exception: t=None
    if t is None or t==s or t.count('\n')!=s.count('\n'): continue
    if t in seen: continue
    seen[t]=n
    open(f'{d}/{pre}{n}.py','w').write('EDITS=%r\n'%(BE+[region(s,t)],)); ok.append(pre+n)
print('\n'.join(ok)); print(len(K),'knobs',len(ok),'applicable',file=sys.stderr)
