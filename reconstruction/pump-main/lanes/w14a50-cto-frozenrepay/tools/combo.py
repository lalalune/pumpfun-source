"""combo.py name=a+b+c ... : e/<name>.py = concatenated edits of e/<a>.py ... (a may be a path stem under e/ or kx/)."""
import sys,os,runpy
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a50-cto-frozenrepay')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a50-cto-frozenrepay'
src=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
for spec in sys.argv[1:]:
    n,parts=spec.split('=')
    E=[]
    for p in parts.split('+'):
        f=f'{O}/e/{p}.py' if os.path.exists(f'{O}/e/{p}.py') else f'{O}/kx/{p}.py'
        E+=[tuple(x) for x in runpy.run_path(f)['EDITS']]
    s=src; ok=True
    for a,b in E:
        if s.count(a)!=1: ok=False; break
        s=s.replace(a,b)
    if not ok: print('#skip',n,file=sys.stderr); continue
    open(f'{O}/e/{n}.py','w').write('EDITS=%r\n'%(E,)); print(n)
