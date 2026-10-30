#!/usr/bin/env python3
"""rec.py <trial> <status> <hypothesis> [note]: record a res.jsonl trial in the shared ledger."""
import sys,json,subprocess
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a20-cto-reloadarm/reconstruction/pump-main/log_attempt.py'
t,st,hyp=sys.argv[1:4]; note=sys.argv[4] if len(sys.argv)>4 else ''
r=None
for l in open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a20-cto-reloadarm/res.jsonl'):
    x=json.loads(l)
    if x['trial']==t: r=x
res=(r or {}).get('res') or {}
ed=open(r['edit']).read() if r else ''
d={'output':'raw-IR capture + rx oracle','target':{'ratio':res.get('ratio'),'slots_diff':res.get('slots_diff'),'cand_bytes':res.get('bytes'),'M':res.get('M')},'notes':'main b174038 (0.63571, M 2122). '+note+' edits: '+ed[:600]}
k='0x22a10-w14-b174038-reloadarm-%s-v1'%t
print(subprocess.run(['python3',L,'record','--lane','w14a20-cto-reloadarm','--approach','reloadarm-source','--target','0x22a10','--dedupe-key',k,'--hypothesis',hyp,'--status',st,'--data',json.dumps(d)],capture_output=True,text=True).stdout[-200:])
