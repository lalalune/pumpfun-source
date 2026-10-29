#!/usr/bin/env python3
"""trial.py <name> <edits.py> [--noir]: copy WT programs/pump (or BASESRC), apply EDITS [(old,new)], capture build, score, oracle metrics."""
import sys,os,shutil,subprocess,runpy,json,re
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-buyexactquote-v3')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w4-buyexactquote-v3'
T=WT+'/reconstruction'
BJ='/private/tmp/claude-501/-Users-shawwalters-Documents-Codex-2026-10-24-pumpfun-source/4381c718-211a-406c-9278-6119c4649998/scratchpad/w3/final/out/score.json'
name,ed=sys.argv[1],sys.argv[2]
basesrc=os.environ.get('BASESRC',WT+'/programs/pump')
dst=f'{OUT}/src/{name}'
if os.path.exists(dst): shutil.rmtree(dst)
shutil.copytree(basesrc,dst,ignore=shutil.ignore_patterns('target'))
E=runpy.run_path(ed)['EDITS']
f=dst+'/src/trade_v3.rs'; s=open(f).read()
for o,n in E:
    pass
for o,n in E:
    c=s.count(o); assert c==1,(c,o[:80]); s=s.replace(o,n)
open(f,'w').write(s)
o=f'{OUT}/out/{name}'; os.makedirs(o,exist_ok=True)
env=dict(os.environ,PUMP_BUILD_SLOTS='10')
r=subprocess.run(['python3',OUT+'/scripts/capture.py',dst,OUT+'/work-ir'+os.environ.get('SLOT',''),o],capture_output=True,text=True,env=env)
open(o+'/capture.log','w').write(r.stdout+r.stderr)
if not os.path.exists(o+'/pump_recovered.ll') or '"ok": false' in r.stdout:
    print('BUILD FAILED'); print('\n'.join(l for l in (r.stdout+r.stderr).splitlines() if 'error' in l)[:3000]); sys.exit(1)
sc=subprocess.run(['python3',T+'/harness/score.py',o+'/unstripped.so','--baseline',BJ,'--json',o+'/score.json','--quiet'],capture_output=True,text=True).stdout.strip().splitlines()[-1]
j=json.loads(sc); print(name,'norm',j['normalized'],'raw',j['raw'],'gains',j['gains'],'losses',j['losses'],'rawloss',j['raw_losses'])
tm=subprocess.run(['python3',T+'/harness/target_metric.py',o+'/unstripped.so','0x1489f8','--sym',r'^pump_recovered::trade::buy_exact_quote$'],capture_output=True,text=True).stdout.strip().splitlines()[0]
t=json.loads(tm); print('  target bytes',t['cand_bytes'],'ratio',t['ratio'],'calls',t['calls_candidate'],'norm',t['normalized_equal'])
# oracle diffslots with this build's IR
ll=o+'/pump_recovered.ll'
sym=re.search(r'define[^@]*@(_ZN14pump_recovered5trade15buy_exact_quote17h[0-9a-f]+E)\(',open(ll).read()).group(1)
r=subprocess.run(['python3',OUT+'/scripts/ir.py',name,'-'],capture_output=True,text=True,env=dict(os.environ,IRBASE=ll,SYM=sym))
print(' ',r.stdout.strip())
for w,sy in (('0x147ba0',r'^pump_recovered::trade::buy$'),('0x14a8a8',r'^pump_recovered::trade::sell$')):
    tm=subprocess.run(['python3',T+'/harness/target_metric.py',o+'/unstripped.so',w,'--sym',sy],capture_output=True,text=True).stdout.strip().splitlines()
    if tm: t=json.loads(tm[0]); print('  sib',w,t['cand_bytes'],t['ratio'])
