#!/usr/bin/env python3
"""ledger_sync.py results.jsonl: record every r3run result not yet in the shared ledger (key 0x22a10-w13-<main>-r3-<label>-v1)."""
import json,sys,subprocess,re
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a15-cto-region3of3/reconstruction/pump-main/log_attempt.py'
for l in open(sys.argv[1]):
    if not l.strip(): continue
    r=json.loads(l)
    if r.get('status')!='built': continue
    key=f"0x22a10-w13-{r['main']}-r3-{re.sub('[^A-Za-z0-9_+]','+',r['label'])}-v1"
    if json.loads(subprocess.run(['python3',L,'check','--dedupe-key',key],capture_output=True,text=True).stdout or '{}').get('duplicate'): continue
    land=r['bytes']==27400 and not r['losses'] and r['n_raw_losses']==0
    st='partial' if land and r['ratio']>0.51228 else ('built' if land else 'rejected')
    data={'output':r.get('out',''),'normalized':r['norm'],'raw':r['raw'],'losses':r['losses'],'raw_losses':r['n_raw_losses'],
          'target':{'ratio':r['ratio'],'slots_diff':r['slots'],'cand_bytes':r['bytes']},'notes':f"regions R1/R2/R3 matched {r['regions']} (regcon.py); sha {r['sha']}"}
    subprocess.run(['python3',L,'record','--lane','w13a15-cto-region3of3','--approach','region3-gene-screen','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f"region-3 gene set [{r['label']}] (w12a14/w13a10 gene library) on main {r['main']} (0.51228)",'--status',st,'--data',json.dumps(data)],capture_output=True)
    print('recorded',key,st)
