#!/usr/bin/env python3
"""rec.py <cell> <status> "<hypothesis>" [notes]: ledger row for a s3cashflag cell from rx/<cell>/res.json + mp.out (+ stacked if present)."""
import sys,json,subprocess,os
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a21-cto-s3cashflag'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a21-cto-s3cashflag/reconstruction/pump-main/log_attempt.py'
c,st,hyp=sys.argv[1:4]; notes=sys.argv[4] if len(sys.argv)>4 else ''
r=json.load(open(f'{O}/rx/{c}/res.json'))
mp={}
try: mp=json.loads(open(f'{O}/rx/{c}/mp.out').read().strip().splitlines()[-1])
except Exception: pass
d={'output':f'{O}/rx/{c}','normalized':None,'raw':None,'losses':[],'raw_losses':[],
   'target':{'ratio':r['ratio'],'slots_diff':r.get('slots_diff'),'cand_bytes':r['bytes']},
   'oracle':'raw-IR capture (capraw identity build) + SDK opt -O3 + slim + SDK llc (w16a08 tools)',
   'M':mp.get('M'),'Mperm':mp.get('Mperm'),'Mhc':mp.get('Mhc'),
   'base':'main 5998913 + S3n (w16a08 e/S3n.py): M 1990 Mperm 2289 Mhc 2296 stacked 2347 @27416',
   'edits':json.load(open(f'{O}/e/{c}.py.json')) if os.path.exists(f'{O}/e/{c}.py.json') else None,
   'notes':notes}
key=f'0x22a10-w16-5998913-s3cashflag-{c}-v1'
p=subprocess.run(['python3',L,'record','--lane','w16a21-cto-s3cashflag','--approach','s3cashflag','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
print(key,p.returncode,p.stdout.strip()[:120],p.stderr.strip()[:200])
