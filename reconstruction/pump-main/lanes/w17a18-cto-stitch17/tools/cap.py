#!/usr/bin/env python3
"""cap.py <name> <genes,comma,sep> <slot> [--base <crate dir>]: copy the lane crate, apply genes17 genes to admin_cto.rs
(line count must not change), capture pre-opt IR (capraw), preslim, fx oracle -> res/cap.jsonl (+ oracle slots).
Experiment only."""
import sys,os,subprocess,json,time,shutil,runpy
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T); sys.path.insert(0,T)
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a18-cto-stitch17'
a=sys.argv[1:]; name=a[0]; genes=[g for g in a[1].split(',') if g]; slot=a[2]
base=OUT+'/basecrate'
if '--base' in a: base=a[a.index('--base')+1]
import genes17
v=f'{OUT}/var/{name}'; shutil.rmtree(v,ignore_errors=True)
subprocess.run(['rsync','-a','--exclude','target',base+'/',v+'/'],check=True)
f=v+'/src/creator/admin_cto.rs'; s=open(f).read(); n0=s.count('\n')
lib=v+'/src/lib.rs'; ls=open(lib).read(); nl0=ls.count('\n')
try:
    s,ls=genes17.apply(s,genes,ls)
except Exception as e:
    r={'name':name,'genes':genes,'err':'gene:'+str(e)[:300]}; print(json.dumps(r)); open(OUT+'/res/cap.jsonl','a').write(json.dumps(r)+'\n'); shutil.rmtree(v,ignore_errors=True); sys.exit(1)
assert s.count('\n')==n0,('line count changed',s.count('\n'),n0)
assert ls.count('\n')==nl0,('lib line count changed')
open(f,'w').write(s); open(lib,'w').write(ls)
os.makedirs(OUT+'/src',exist_ok=True); open(f'{OUT}/src/{name}.rs','w').write(s)
w=f'{OUT}/work{slot}'; os.makedirs(w,exist_ok=True)
for p in __import__('glob').glob(w+'/target*/*/release/deps/pump_recovered*.ll'): os.remove(p)
cap=f'{OUT}/ir/cap_{name}'; shutil.rmtree(cap,ignore_errors=True)
t0=time.time(); env=dict(os.environ,PUMP_BUILD_SLOTS='10')
for att in range(3):
    lg=open(f'{OUT}/ir/cap_{name}.log','w')
    subprocess.run(['python3',T+'/capraw.py',v,w,cap],stdout=lg,stderr=subprocess.STDOUT,env=env); lg.close()
    if os.path.exists(cap+'/raw.ll'): break
    txt=open(f'{OUT}/ir/cap_{name}.log').read()
    bl=cap+'/build.log'
    if os.path.exists(bl): txt+=open(bl,errors='replace').read()
    if any(k in txt for k in ('ENFILE','Too many open files','temporarily unavailable','cannot lock ref')): time.sleep(20); continue
    break
shutil.rmtree(v,ignore_errors=True)
if not os.path.exists(cap+'/raw.ll'):
    txt=''
    bl=cap+'/build.log'
    if os.path.exists(bl): txt=open(bl,errors='replace').read()
    import re
    errs=[l for l in txt.split('\n') if l.startswith('error')][:5]
    r={'name':name,'genes':genes,'err':'capture failed','detail':errs}; print(json.dumps(r)); open(OUT+'/res/cap.jsonl','a').write(json.dumps(r)+'\n'); sys.exit(1)
tc=time.time()-t0
os.replace(cap+'/raw.ll',f'{OUT}/ir/{name}.ll'); shutil.rmtree(cap,ignore_errors=True)
env2=dict(os.environ,SURV=OUT+'/data/surv-1647da0.txt')
subprocess.run(['python3',T+'/preslim.py',f'{OUT}/ir/{name}.ll',f'{OUT}/ir/{name}.s.ll','keep'],env=env2,stdout=subprocess.DEVNULL,check=True)
os.remove(f'{OUT}/ir/{name}.ll')
import fx, oracle
r=fx.run(open(f'{OUT}/ir/{name}.s.ll').read(),name)
if 'err' not in r:
    b=open(f'{OUT}/fx/{name}/fn.bin','rb').read()
    rr,sd=oracle.metric(b,oracle.orig_window()); r['slots']=sd
r['genes']=genes; r['cap_secs']=round(tc,1)
print(json.dumps(r)); open(OUT+'/res/cap.jsonl','a').write(json.dumps(r)+'\n')
