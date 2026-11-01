#!/usr/bin/env python3
"""capv.py <varsmodule> <name> <slot>: copy main crate, apply a variant's edits (line count kept), capture pre-opt IR -> ir/<name>.ll"""
import sys,os,runpy,subprocess,shutil,glob,time
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.environ.get('LANE_OUT',os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w17a06-shim-irbeam'))
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a06-shim-irbeam'
vm,name,slot=sys.argv[1],sys.argv[2],sys.argv[3]
V=runpy.run_path(vm)['V']; ed=V[name]
src=os.environ.get('SRCB',WT+'/programs/pump')
v=f'{OUT}/var/{name}'; shutil.rmtree(v,ignore_errors=True)
subprocess.run(['rsync','-a','--exclude','target',src+'/',v+'/'],check=True)
files={'cto':v+'/src/creator/admin_cto.rs','lib':v+'/src/lib.rs'}
for f in set(e[0] for e in ed):
    p=files[f]; s=open(p).read(); n0=s.count('\n')
    for ff,a,b in ed:
        if ff!=f: continue
        c=s.count(a); assert c==1,(name,c,a[:100]); s=s.replace(a,b)
    assert s.count('\n')==n0,(name,'line count changed')
    open(p,'w').write(s)
w=f'{OUT}/work{slot}'; os.makedirs(w,exist_ok=True)
for p in glob.glob(w+'/target*/*/release/deps/pump_recovered*.ll'): os.remove(p)
cap=f'{OUT}/ir/cap_{name}'; shutil.rmtree(cap,ignore_errors=True); t0=time.time()
for attempt in range(3):
    r=subprocess.run(['python3',T+'/capraw.py',v,w,cap],capture_output=True,text=True,env=dict(os.environ,PUMP_BUILD_SLOTS='10'))
    if os.path.exists(cap+'/raw.ll'): break
    log=open(cap+'/build.log').read() if os.path.exists(cap+'/build.log') else r.stdout[-500:]+r.stderr[-500:]
    if any(k in log for k in ('ENFILE','Too many open files','temporarily unavailable','cannot lock ref')): time.sleep(20); continue
    break
if os.path.exists(cap+'/raw.ll'):
    os.rename(cap+'/raw.ll',f'{OUT}/ir/{name}.ll'); shutil.rmtree(cap,ignore_errors=True); shutil.rmtree(v,ignore_errors=True)
    print('captured',name,round(time.time()-t0),'s',flush=True)
else:
    log=open(cap+'/build.log').read() if os.path.exists(cap+'/build.log') else ''
    i=log.find('error'); open(f'{OUT}/ir/{name}.err','w').write(log[max(0,i-200):i+1500] if i>=0 else log[-2000:]+r.stdout[-500:]+r.stderr[-500:])
    print('FAILED',name,flush=True); shutil.rmtree(v,ignore_errors=True)
