#!/usr/bin/env python3
"""rec.py <name> <hypothesis> [status]: record an oracle trial from res.jsonl in the shared ledger."""
import sys,json,subprocess,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a01-cto-acctlive')
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a01-cto-acctlive/reconstruction/pump-main/log_attempt.py'
n,h=sys.argv[1],sys.argv[2]; MAIN=os.environ.get("MAIN","53abf28 (0.62672)"); st=sys.argv[3] if len(sys.argv)>3 else 'rejected'
d=[json.loads(l) for l in open(O+'/res.jsonl') if json.loads(l)['n']==n][-1]
r=d['rx'] or {}; f=d['llcb'] or {}; rl=d['rl'] or {}
note=f"raw-IR capture + rx opt/llc oracle (= build tokens) on main {MAIN}. clonefeat {f.get('cf')} (orig 6/2, main 2/6); stack reloads {rl.get('reloads')} (orig 537, main 505); tag==2 regs {rl.get('tag2')} (orig r7 21, main r7 18); eq_main={r.get('eq_main')}"
key='0x22a10-w14-'+MAIN[:7]+f'-acctlive-{n}-v1'
data={'output':O+'/rx/'+n,'target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes')},'notes':note}
subprocess.run(['python3',L,'record','--lane','w14a01-cto-acctlive','--approach','acct-liverange','--target','0x22a10','--dedupe-key',key,'--hypothesis',h,'--status',st,'--data',json.dumps(data)],check=True)
