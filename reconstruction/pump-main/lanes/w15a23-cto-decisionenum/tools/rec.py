#!/usr/bin/env python3
"""rec.py: record res.jsonl rows not yet recorded (state in recorded.txt) using hyp.json {name: hypothesis}"""
import json,subprocess,os
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a23-cto-decisionenum')
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a23-cto-decisionenum/reconstruction/pump-main/log_attempt.py'
H=json.load(open(OUT+'/hyp.json')); done=set(open(OUT+'/recorded.txt').read().split()) if os.path.exists(OUT+'/recorded.txt') else set()
extra=json.load(open(OUT+'/extra.json')) if os.path.exists(OUT+'/extra.json') else {}
for l in open(OUT+'/res.jsonl'):
    r=json.loads(l); n=r['name']
    if n in done or n not in H: continue
    lo=r.get('losses'); rl=r.get('raw_losses'); lo=lo if isinstance(lo,int) else len(lo or []); rl=rl if isinstance(rl,int) else len(rl or [])
    d={'output':'t/'+n,'normalized':r.get('norm'),'raw':r.get('raw'),'losses':lo,'raw_losses':rl,'target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots'),'cand_bytes':r.get('bytes')},'notes':'main 9120883 0.67376@27400 (true-LCS ---2255 rfj3007, Mperm 2292). '+extra.get(n,'')}
    st='rejected' if (r.get('ratio') or 0)<=0.67376 else 'built'
    p=subprocess.run(['python3',L,'record','--lane','w15a23-cto-decisionenum','--approach','decisionenum','--target','0x22a10','--dedupe-key',f'0x22a10-w15-9120883-decisionenum-{n}-v1','--hypothesis',H[n],'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
    if p.returncode==0: done.add(n)
    else: print(n,p.stderr[-300:])
open(OUT+'/recorded.txt','w').write('\n'.join(sorted(done)))
print(len(done),'recorded')
