#!/usr/bin/env python3
"""rec.py <mech> <status> <ratio> <bytes> <hypothesis> <notes>: ledger record for w14a04 on main 23322b0."""
import sys,subprocess,json
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a04-cto-hkclone/reconstruction/pump-main/log_attempt.py'
mech,st,r,b,hyp,notes=sys.argv[1:7]
key=f'0x22a10-w14-23322b0-hkclone-{mech}-v1'
d={'output':'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a04-cto-hkclone','normalized':1034,'raw':1034,'losses':[],'raw_losses':[],'target':{'ratio':float(r),'slots_diff':0,'cand_bytes':int(b)},'notes':notes}
subprocess.run(['python3',L,'record','--lane','w14a04-cto-hkclone','--approach','hkclone','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status',st,'--data',json.dumps(d)],check=False)
