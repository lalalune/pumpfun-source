#!/usr/bin/env python3
"""rec.py <name> <result line>: ledger row for a jointrb oracle trial (hypothesis from e/<name>.py docstring HYP)."""
import sys,os,json,re,subprocess,runpy
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a13-cto-jointraceback'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a13-cto-jointraceback/reconstruction/pump-main/log_attempt.py'
n,line=sys.argv[1],sys.argv[2]
try: hyp=runpy.run_path(f'{OUT}/e/{n}.py').get('HYP',n)
except Exception: hyp=n
m=re.search(r'bytes (\d+) M (\d+) ratio ([\d.]+) skM (\d+)',line); sd=re.search(r'"slots_diff": (\d+)',line)
if m: B,M,R,sk=int(m[1]),int(m[2]),float(m[3]),int(m[4]); st='rejected' if not (R>0.67376 and B==27400) else 'analyzed'
else: B=M=R=sk=None; st='compile-failed'
data={'output':f'{OUT}/rx/{n}','target':{'ratio':R,'slots_diff':int(sd[1]) if sd else None,'cand_bytes':B,'M':M,'skM':sk},
      'notes':f'jointrb raw-IR oracle (capraw+rx opt/llc) on main 86e2a6b (0.67376 @27400): {line[:300]}'}
subprocess.run(['python3',L,'record','--lane','w15a13-cto-jointraceback','--approach','jointrb','--target','0x22a10','--dedupe-key',f'0x22a10-w15-86e2a6b-jointrb-{n}-v1','--hypothesis',f'jointrb region rewrite on 86e2a6b: {hyp}','--status',st,'--data',json.dumps(data)],capture_output=True)
