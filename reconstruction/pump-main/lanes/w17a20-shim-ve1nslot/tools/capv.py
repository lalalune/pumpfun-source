#!/usr/bin/env python3
"""capv.py <name> <slot>: copy the worktree crate, apply tools/vars.py V[name] (line count kept), capture pre-opt IR,
preslim, fx (exact slim oracle). Experiment only."""
import sys,os,runpy,subprocess,shutil,glob,time,json
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T)
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a20-shim-ve1nslot'
name,slot=sys.argv[1],sys.argv[2]
V=runpy.run_path(T+'/vars.py')['V']; ed=V[name]
v=f'{OUT}/var/{name}'; shutil.rmtree(v,ignore_errors=True)
subprocess.run(['rsync','-a','--exclude','target',WT+'/programs/pump/',v+'/'],check=True)
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
cap=f'{OUT}/ir/cap_{name}'; shutil.rmtree(cap,ignore_errors=True); os.makedirs(cap); t0=time.time()
for attempt in range(3):
    r=subprocess.run(['python3',OUT+'/t6/capraw.py',v,w,cap],capture_output=True,text=True,env=dict(os.environ,PUMP_BUILD_SLOTS='10'))
    if os.path.exists(cap+'/raw.ll'): break
    log=open(cap+'/build.log').read() if os.path.exists(cap+'/build.log') else r.stdout[-500:]+r.stderr[-500:]
    if any(k in log for k in ('ENFILE','Too many open files','temporarily unavailable','cannot lock ref')): time.sleep(20); continue
    break
if not os.path.exists(cap+'/raw.ll'):
    log=open(cap+'/build.log').read() if os.path.exists(cap+'/build.log') else ''
    i=log.find('error['); i=i if i>=0 else log.find('error:')
    open(f'{OUT}/ir/{name}.err','w').write(log[max(0,i-200):i+2500] if i>=0 else log[-2000:])
    print(json.dumps({'name':name,'err':'capture failed'})); sys.exit(1)
sl=f'{OUT}/ir/{name}.slim.ll'
subprocess.run(['python3',OUT+'/t6/preslim.py',cap+'/raw.ll',sl,'keep'],env=dict(os.environ,SURV=OUT+'/t6/surv-1647da0.txt'),check=True,capture_output=True)
shutil.rmtree(cap,ignore_errors=True); shutil.rmtree(v,ignore_errors=True)
r=subprocess.run(['python3',OUT+'/t6/fx.py',sl,name,'--keep'],capture_output=True,text=True,env=dict(os.environ,LANE_OUT=OUT))
print(r.stdout.strip(), 'cap_secs', round(time.time()-t0))
