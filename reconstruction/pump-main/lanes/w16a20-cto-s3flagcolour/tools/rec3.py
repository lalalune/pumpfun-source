#!/usr/bin/env python3
"""rec3.py <cell> <status> <hypothesis> <notes> [json-extra]: one ledger row for lane w16a20-cto-s3flagcolour"""
import sys,subprocess,json
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a20-cto-s3flagcolour/reconstruction/pump-main/log_attempt.py'
cell,st,hyp,notes=sys.argv[1:5]; extra=json.loads(sys.argv[5]) if len(sys.argv)>5 else {}
key=f'0x22a10-w16-5998913-s3flagcolour-{cell}-v1'
c=subprocess.run(['python3',L,'check','--dedupe-key',key],capture_output=True,text=True)
if json.loads(c.stdout or "{}").get("duplicate"): print("dup",key); sys.exit(0)
d={'output':'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour','normalized':1034,'raw':1034,'losses':[],'raw_losses':[],'notes':notes}
d.update(extra)
r=subprocess.run(['python3',L,'record','--lane','w16a20-cto-s3flagcolour','--approach','s3flagcolour','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
print(key, r.returncode, (r.stdout+r.stderr).strip()[:200])
