#!/usr/bin/env python3
"""rec26.py kind name status hyp note [ratio bytes]: one ledger row (approach o2tfg3repay, wave-16 continuation)."""
import sys,json,subprocess
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a25-cto-o2tfg3repay'
kind,name,st,hyp,note=sys.argv[1:6]
tgt={}
if len(sys.argv)>7: tgt={'ratio':float(sys.argv[6]),'cand_bytes':int(sys.argv[7]),'slots_diff':None}
key=f'0x22a10-w15-9120883-o2tfg3repay-{kind}-{name}-v1'
d={'output':f'lanes/w15a25-cto-o2tfg3repay/{name}','normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':tgt,'notes':note}
r=subprocess.run(['python3',WT+'/reconstruction/pump-main/log_attempt.py','record','--lane','w15a25-cto-o2tfg3repay','--approach','o2tfg3repay','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
print(key, r.returncode, r.stdout.strip()[:100], r.stderr.strip()[:200])
