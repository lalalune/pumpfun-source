#!/usr/bin/env python3
"""rec.py: record each t/as2.jsonl row (not yet recorded) into the shared ledger."""
import json,subprocess,os
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a95-cto-devol334/'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a95-cto-devol334/reconstruction/pump-main/log_attempt.py'
done=set(open(O+'t/recorded2.txt').read().split()) if os.path.exists(O+'t/recorded2.txt') else set()
for l in open(O+'t/as2.jsonl'):
    d=json.loads(l); n=d['name']
    if n in done: continue
    try: ed=open(O+'v/%s.py'%n).read().strip()[:900]
    except Exception: ed='?'
    st='compile-failed' if d.get('error') else ('rejected' if d.get('M',0)<2245 or d.get('bytes')!=27400 else 'built')
    hyp='devol334: ordinary spelling replacing the line-334 read_volatile placeholder; base B2 = 13fe453 minus vol334. '+ed
    data={'normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':{'ratio':d.get('ratio'),'slots_diff':d.get('slots_diff'),'cand_bytes':d.get('bytes')},
          'notes':'raw-IR capture + opt/llc oracle on B2; M %s @%s (need >= main M @27400; main 13fe453 M 2245)'%(d.get('M'),d.get('bytes'))}
    r=subprocess.run(['python3',L,'record','--lane','w14a95-cto-devol334','--approach','devol334','--target','0x22a10',
        '--dedupe-key','0x22a10-w14-13fe453-devol334-%s-v1'%n,'--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
    if r.returncode==0: done.add(n)
    else: print(n,r.stderr[-200:])
open(O+'t/recorded2.txt','w').write('\n'.join(sorted(done))+'\n')
print(len(done),'recorded')
