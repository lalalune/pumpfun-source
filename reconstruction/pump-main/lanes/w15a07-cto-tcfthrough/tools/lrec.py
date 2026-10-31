#!/usr/bin/env python3
"""lrec.py <key> <status> <hyp> <rxname|-> <note>: ledger record for this lane"""
import json,sys,os,subprocess
k,st,hyp,f,note=sys.argv[1:6]
p=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a07-cto-tcfthrough/rx/%s/res.json'%f)
d=json.load(open(p)) if f!='-' and os.path.exists(p) else {}
data={"output":p if d else "","normalized":1034,"raw":1034,"losses":[],"raw_losses":[],"target":{"ratio":d.get('ratio'),"slots_diff":d.get('slots_diff'),"cand_bytes":d.get('bytes')},"tcf":{x:d[x] for x in d if x.endswith('_tcf') or x in('M','fM','sk')},"notes":note}
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a07-cto-tcfthrough/reconstruction/pump-main/log_attempt.py'
r=subprocess.run(['python3',L,'record','--lane','w15a07-cto-tcfthrough','--approach','tcfthrough','--target','0x22a10','--dedupe-key','0x22a10-w15-90300f9-tcfthrough-%s-v1'%k,'--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
print(k, r.returncode, (r.stdout+r.stderr).strip()[-120:])
