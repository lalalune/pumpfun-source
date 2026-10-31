#!/usr/bin/env python3
"""recmr.py <mrfile> <hypothesis-prefix> [desc.json]: record each mr row (not m) as a rejected oracle trial on main 39eb377."""
import sys,json,subprocess
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a58-cto-tafterlevy/reconstruction/pump-main/log_attempt.py'
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a58-cto-tafterlevy'
mf,hp=sys.argv[1:3]; D=json.load(open(sys.argv[3])) if len(sys.argv)>3 else {}
for l in open(mf):
    r=l.split()
    if len(r)<7 or r[0]=='m': continue
    n=r[0]; M=int(r[4]); st='rejected'
    data={'output':f'{O}/rx/{n}','losses':[],'raw_losses':[],'target':{'ratio':float(r[1]),'slots_diff':None,'cand_bytes':int(r[2])},
      'notes':f'raw-IR capture+opt+llc oracle on main 39eb377 (m eq_main true, 0.66477 M 2219 @27400): ratio {r[1]} bytes {r[2]} M {r[4]} jM {r[6]}'}
    k=f'0x22a10-w14-39eb377-tafterlevy-{n}-v1'
    c=subprocess.run(['python3',L,'record','--lane','w14a58-cto-tafterlevy','--approach','tafterlevy','--target','0x22a10','--dedupe-key',k,'--hypothesis',hp+' '+D.get(n,n),'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
    if c.returncode: print(k,c.stderr[-200:])
print('done')
