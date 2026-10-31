#!/usr/bin/env python3
"""rec.py <res.jsonl> <keyprefix> <hypothesis prefix> <notes>: record each row in the ledger (status rejected unless ratio>main)."""
import sys,json,subprocess
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a40-cto-pdapscan/reconstruction/pump-main/log_attempt.py'
res,kp,hp,nt=sys.argv[1:5]
for l in open(res):
    try: d=json.loads(l)
    except: continue
    if 'name' not in d: continue
    data={'output':'rx/'+d['name'],'target':{'ratio':d.get('ratio'),'slots_diff':d.get('slots_diff'),'cand_bytes':d.get('bytes')},'notes':nt}
    st='compile-failed' if 'error' in d else 'rejected'
    subprocess.run(['python3',L,'record','--lane','w14a40-cto-pdapscan','--approach','pda-pscan','--target','0x22a10','--dedupe-key',f"{kp}-{d['name']}-v1",'--hypothesis',f"{hp} {d['name']}",'--status',st,'--data',json.dumps(data)],capture_output=True)
print('ok')
