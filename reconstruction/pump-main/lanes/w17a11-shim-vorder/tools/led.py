#!/usr/bin/env python3
"""led.py <key-suffix> <status> <hypothesis> <notes> [json-metrics]: record a ledger row for this lane."""
import sys,json,subprocess
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a11-shim-vorder/reconstruction/pump-main/log_attempt.py'
k,st,h,n=sys.argv[1:5]; m=json.loads(sys.argv[5]) if len(sys.argv)>5 else {}
data={'output':'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a11-shim-vorder','notes':n}; data.update(m)
key=('0x22a10-w17-%s-vorder-%s-v1'%(__import__('os').environ.get('BSHA','d4dfb04'),k))
r=subprocess.run(['python3',L,'record','--lane','w17a11-shim-vorder','--approach','shimvorder','--target','0x22a10','--dedupe-key',key,
  '--hypothesis',h,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
print(r.returncode,(r.stdout+r.stderr).strip()[-160:])
