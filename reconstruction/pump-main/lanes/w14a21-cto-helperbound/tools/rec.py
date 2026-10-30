#!/usr/bin/env python3
"""rec.py <name> <status> <hypothesis> <notes>: record a raw-IR oracle trial in the ledger using rx/<name>/res.json"""
import sys,json,subprocess,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a21-cto-helperbound')
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a21-cto-helperbound/reconstruction/pump-main/log_attempt.py'
n,st,hy,no=sys.argv[1:5]; base=os.environ.get('BASE7','b174038')
try: r=json.load(open(f'{O}/rx/{n}/res.json'))
except Exception: r={}
d={'output':f'{O}/rx/{n}','target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes')},'notes':'raw-IR capture+opt+llc oracle (eq_main verified) on main '+base+'; '+no}
k=f'0x22a10-w14-{base}-helperbound-{n}-v1'
subprocess.run(['python3',L,'record','--lane','w14a21-cto-helperbound','--approach','helperbound','--target','0x22a10','--dedupe-key',k,'--hypothesis',hy,'--status',st,'--data',json.dumps(d)],check=True,capture_output=True)
print('recorded',k)
