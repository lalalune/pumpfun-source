import sys,os
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a27-cto-hvatalit'
src=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
base,d,kf=sys.argv[1:4]; os.makedirs(d,exist_ok=True)
g={}; exec(open(base).read(),g); BE=g['EDITS']; s=src
for a,b in BE: assert s.count(a)==1; s=s.replace(a,b)
g2={}; exec(open(kf).read(),g2)
for n,e in g2['K'].items():
    t=s; bad=None
    for a,b in e:
        if t.count(a)!=1 or a.count('\n')!=b.count('\n'): bad=(a[:60],t.count(a)); break
        t=t.replace(a,b)
    if bad: print('#skip',n,bad,file=sys.stderr); continue
    open(f'{d}/{n}.py','w').write('EDITS=%r\n'%(BE+e,)); print(n)
