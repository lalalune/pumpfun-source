#!/usr/bin/env python3
"""rec.py <name> <hypothesis> [status]: record an oracle trial from res.jsonl in the shared ledger."""
import sys,json,subprocess,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a05-cto-sibclone')
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a05-cto-sibclone/reconstruction/pump-main/log_attempt.py'
n,h=sys.argv[1],sys.argv[2]; st=sys.argv[3] if len(sys.argv)>3 else 'rejected'
base=os.environ.get('BASE7','23322b0'); mr=os.environ.get('MAINR','0.62882')
d=[json.loads(l) for l in open(O+'/res.jsonl') if json.loads(l)['n']==n][-1]
r=d['rx'] or {}; ab=d['abs'] or {}; rl=d['rl'] or {}
note=f"raw-IR capture + opt/llc oracle (= build tokens) on main {base} ({mr}, fm 0.72049 rm 0.84781, reloads 506). fm {ab.get('fm')} rm {ab.get('rm')} reloads {rl.get('reloads')} (orig 537); eq_main={r.get('eq_main')}; err={r.get('error')}"
key=f'0x22a10-w14-{base}-sibclone-{n}-v1'
data={'output':O+'/rx/'+n,'target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes')},'notes':note}
subprocess.run(['python3',L,'record','--lane','w14a05-cto-sibclone','--approach','sibling-clone-idiom','--target','0x22a10','--dedupe-key',key,'--hypothesis',h,'--status',st,'--data',json.dumps(data)],check=True,stdout=subprocess.DEVNULL)
print(key)
