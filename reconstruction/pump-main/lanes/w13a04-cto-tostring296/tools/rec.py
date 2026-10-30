#!/usr/bin/env python3
"""rec.py <variant> <mech-key> <status> <hypothesis> [note]"""
import sys,json,subprocess
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a04-cto-tostring296'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a04-cto-tostring296/reconstruction/pump-main/log_attempt.py'
v,key,st,hyp=sys.argv[1:5]; note=sys.argv[5] if len(sys.argv)>5 else ''
d=json.load(open(f'{OUT}/t/{v}.json')); a=d.get('admin_cto') or {}
data={'output':f'{OUT}/t/{v}','normalized':d.get('normalized'),'raw':d.get('raw'),'losses':d.get('losses',[]),'raw_losses':len(d.get('raw_losses',[])),
 'target':{'ratio':a.get('ratio'),'slots_diff':a.get('slots_diff'),'cand_bytes':a.get('cand_bytes')},'notes':note}
k=f'0x22a10-w13-4394685-tostring296-{key}-v1'
subprocess.run(['python3',L,'record','--lane','w13a04-cto-tostring296','--approach','tostring296','--target','0x22a10','--dedupe-key',k,'--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],check=True,capture_output=True)
print('recorded',k)
