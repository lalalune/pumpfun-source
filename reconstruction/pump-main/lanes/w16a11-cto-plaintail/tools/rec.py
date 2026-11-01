#!/usr/bin/env python3
"""rec.py <key-suffix> <status> <hypothesis> <note> [json-target]: one plaintail ledger row (experiment analysis)."""
import sys,subprocess,json
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a11-cto-plaintail/reconstruction/pump-main/log_attempt.py'
k,st,h,n=sys.argv[1:5]; tgt=json.loads(sys.argv[5]) if len(sys.argv)>5 else {}
key=f'0x22a10-w16-1f4e396-plaintail-{k}-v1'
c=subprocess.run(['python3',L,'check','--dedupe-key',key],capture_output=True,text=True)
data={'output':'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a11-cto-plaintail','target':tgt,'notes':n}
r=subprocess.run(['python3',L,'record','--lane','w16a11-cto-plaintail','--approach','plaintail','--target','0x22a10','--dedupe-key',key,'--hypothesis',h,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
print(key, r.returncode, (r.stdout+r.stderr).strip()[-200:])
