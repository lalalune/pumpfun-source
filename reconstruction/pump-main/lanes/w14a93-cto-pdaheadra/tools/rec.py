#!/usr/bin/env python3
"""rec.py <trial> <status> <hypothesis> <json-target> [notes]: ledger record for this lane (main ecea702)."""
import sys,json,subprocess
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a93-cto-pdaheadra/reconstruction/pump-main/log_attempt.py'
t,st,hy,tg=sys.argv[1:5]; notes=sys.argv[5] if len(sys.argv)>5 else ''
key=f'0x22a10-w14-ecea702-pdaheadra-{t}-v1'
c=subprocess.run(['python3',L,'check','--dedupe-key',key],capture_output=True,text=True)
d={'output':'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a93-cto-pdaheadra/rx/'+t,'target':json.loads(tg),'notes':notes,'oracle':'raw-IR capture + opt -O3 + llc (rx.py); private RAPRIO llc for forces'}
r=subprocess.run(['python3',L,'record','--lane','w14a93-cto-pdaheadra','--approach','pdaheadra','--target','0x22a10','--dedupe-key',key,'--hypothesis',hy,'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
print(key, r.returncode, (r.stdout+r.stderr).strip()[-200:])
