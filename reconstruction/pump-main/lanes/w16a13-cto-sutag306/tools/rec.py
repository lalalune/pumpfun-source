#!/usr/bin/env python3
"""rec.py <form> <status> <hypothesis> <note> [ratio bytes slots]: one ledger row (approach sutag306)."""
import sys,json,subprocess
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a13-cto-sutag306'
form,st,hyp,note=sys.argv[1:5]
d={'notes':note}
if len(sys.argv)>5:
    d['target']={'ratio':float(sys.argv[5]),'bytes':int(sys.argv[6]),'cand_bytes':int(sys.argv[6]),'slots_diff':(int(sys.argv[7]) if len(sys.argv)>7 and sys.argv[7]!='None' else None)}
key=f'0x22a10-w16-1f4e396-sutag306-{form}-v1'
r=subprocess.run(['python3',WT+'/reconstruction/pump-main/log_attempt.py','record','--lane','w16a13-cto-sutag306','--approach','sutag306','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
print(key, r.returncode, (r.stdout+r.stderr).strip()[-300:])
