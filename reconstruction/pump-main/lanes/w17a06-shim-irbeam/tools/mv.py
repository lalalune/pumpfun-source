#!/usr/bin/env python3
"""mv.py <varsmodule> <name> <slot>: copy worktree crate, apply a variant's edits, run measure.sh -> t/<name>; print summary."""
import sys,os,runpy,subprocess,shutil,json
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T)
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a06-shim-irbeam'
TOOLS='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools'
vm,name,slot=sys.argv[1],sys.argv[2],sys.argv[3]
ed=runpy.run_path(vm)['V'][name]
src=os.environ.get('SRCB',WT+'/programs/pump')
v=f'{OUT}/var/m_{name}'; shutil.rmtree(v,ignore_errors=True)
subprocess.run(['rsync','-a','--exclude','target',src+'/',v+'/'],check=True)
files={'cto':v+'/src/creator/admin_cto.rs','lib':v+'/src/lib.rs'}
for f in set(e[0] for e in ed):
    p=files[f]; s=open(p).read(); n0=s.count('\n')
    for ff,a,b in ed:
        if ff!=f: continue
        c=s.count(a); assert c==1,(name,c,a[:100]); s=s.replace(a,b)
    assert s.count('\n')==n0,(name,'line count changed')
    open(p,'w').write(s)
t=f'{OUT}/t/{name}'; os.makedirs(t,exist_ok=True)
r=subprocess.run([TOOLS+'/measure.sh',v,f'{OUT}/work{slot}',t],capture_output=True,text=True,env=dict(os.environ,PUMP_BUILD_SLOTS='10'))
line=(r.stdout.strip().splitlines() or [''])[-1]
open(t+'/m.json','w').write(line)
try:
    d=json.loads(line); c=d.get('admin_cto',{})
    print(json.dumps({'name':name,'ok':d.get('ok'),'ratio':c.get('ratio'),'slots':c.get('slots_diff'),'bytes':c.get('cand_bytes'),'calls':c.get('calls_candidate'),'norm':d.get('normalized'),'raw':d.get('raw'),'losses':d.get('losses'),'raw_losses':d.get('raw_losses'),'gains':d.get('gains'),'sha':d.get('sha'),'err':str(d.get('error'))[-300:] if not d.get('ok') else None}))
except Exception as e: print(json.dumps({'name':name,'err':line[-500:]+r.stderr[-500:]}))
shutil.rmtree(v,ignore_errors=True)
