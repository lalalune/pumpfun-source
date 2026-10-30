#!/usr/bin/env python3
"""rec.py name status "hypothesis" ["notes"]: record an rx oracle trial from res.jsonl into the shared ledger."""
import sys,json,subprocess
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a42-cto-entrycopy3'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a42-cto-entrycopy3/reconstruction/pump-main/log_attempt.py'
import os; BASE=os.environ.get('BASE','6ac6f9b (k1 0.56291)')
n,st,hyp=sys.argv[1:4]; notes=sys.argv[4] if len(sys.argv)>4 else ''
r=None
for l in open(O+'/res.jsonl'):
    try: d=json.loads(l)
    except: continue
    if d.get('name')==n: r=d
edits=open(O+'/e/%s.py'%n).read() if r else ''
data={'output':O+'/rx/'+n,'target':{'ratio':r and r.get('ratio'),'slots_diff':r and r.get('slots_diff'),'cand_bytes':r and r.get('bytes')},
      'notes':'raw-IR capture + rx opt/llc oracle (= build tokens) on main '+BASE+'. '+notes+' edits: '+edits.split('\n',1)[1][:600]}
subprocess.run(['python3',L,'record','--lane','w13a42-cto-entrycopy3','--approach','entrycopy3','--target','0x22a10',
  '--dedupe-key','0x22a10-w13-%s-entrycopy3-%s-v1'%(BASE[:7],n),'--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],check=True,capture_output=True)
print(n,r)
