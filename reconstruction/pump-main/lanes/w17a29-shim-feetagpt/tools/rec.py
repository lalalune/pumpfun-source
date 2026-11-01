#!/usr/bin/env python3
# rec.py <key-suffix> <status> <hyp> <M> <bytes> <note> : record a ledger row for this lane (main 53ec7fb)
import sys,subprocess,json
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a29-shim-feetagpt/reconstruction/pump-main/log_attempt.py'
k,st,hyp,M,B,note=sys.argv[1:7]
M=int(M) if M not in ('','-') else None; B=int(B) if B not in ('','-') else None
ratio=round(2*M/(6676+((B or 27400)-27400)/8),5) if M else None
data={'output':'slim oracle (w17a06 capraw/preslim/fx) on main 53ec7fb53','normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':{'ratio':ratio,'M':M,'cand_bytes':B},'notes':note}
key='0x22a10-w17-53ec7fb-feetagpt-%s-v1'%k
r=subprocess.run(['python3',L,'record','--lane','w17a29-shim-feetagpt','--approach','feetagpt','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
print(key, r.returncode, (r.stdout+r.stderr).strip()[-200:])
