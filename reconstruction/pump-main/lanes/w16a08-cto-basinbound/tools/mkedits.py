import json,runpy,re,sys
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound'
g=runpy.run_path(O+'/e/g25.py')['G']
# w15a11 gen.py V dict (v14/v21/v26)
src=open(O+'/x/w15a11-cto-valtraceback/e/gen.py').read()
V={}
for k in ('v14','v21','v26'):
    m=re.search(r"'%s':(\[\(.*?\)\]),\n"%k,src); V[k]=eval(m.group(1))
ov1a=runpy.run_path(O+'/x/w15a20-cto-ovarmpin/e/ov1a.py')['EDITS']
S={'m0':[], 'T289n':g['p289n'], 'X1':g['p289n']+g['sn'], 'Y2':g['v27'], 'Z2':g['zmw'], 'B2':g['h296in']+g['p289h'],
   'F2':g['rar']+g['f2has'], 'v14':V['v14'], 'v21':V['v21'], 'v26':V['v26'], 'ov1a':[tuple(x) for x in ov1a]}
f=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a08-cto-basinbound/programs/pump/src/creator/admin_cto.rs').read()
for k,v in S.items():
    s=f; n0=s.count('\n')
    for a,b in v:
        c=s.count(a); assert c==1,(k,c,a[:100]); s=s.replace(a,b)
    assert s.count('\n')==n0,(k,'lines')
    open(f'{O}/e/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
    print(k,len(v),'ok')
