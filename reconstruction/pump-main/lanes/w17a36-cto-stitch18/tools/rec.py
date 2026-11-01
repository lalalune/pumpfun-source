#!/usr/bin/env python3
"""rec.py [mainM]: record every res/cap.jsonl row not yet recorded into the shared ledger (approach stitch18).
Each row carries 'base' (main sha7 of the crate it was captured on) and 'mainM' (main's oracle M on that base)."""
import sys,os,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T)
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a36-cto-stitch18'
L=WT+'/reconstruction/pump-main/log_attempt.py'
done=set(open(OUT+'/res/recorded.txt').read().split()) if os.path.exists(OUT+'/res/recorded.txt') else set()
for l in open(OUT+'/res/cap.jsonl'):
    r=json.loads(l); n=r['name']
    if n in done: continue
    base=r.get('base','53ec7fb'); mM=r.get('mainM',2295)
    key=f'0x22a10-w17-{base}-stitch18-{n}-v1'
    genes='+'.join(r.get('genes',[])) or 'main'
    if 'err' in r:
        st='compile-failed'; data={'output':f'{OUT}/fx/{n}','notes':f"genes {genes}: {r['err']} {r.get('detail','')}"[:500]}
    else:
        st='analyzed'
        data={'output':f'{OUT}/fx/{n}','target':{'ratio':r['ratio'],'slots_diff':r.get('slots'),'cand_bytes':r['bytes']},
              'notes':f"slim pre-opt oracle (capraw+preslim+fx) on main {base}: genes {genes} -> M {r['M']} @{r['bytes']} (dM {r['M']-mM:+d} vs main {mM}, dB {r['bytes']-27400:+d}), oracle slots {r.get('slots')}, sig {r.get('sig')}"}
    cmd=['python3',L,'record','--lane','w17a36-cto-stitch18','--approach','stitch18','--target','0x22a10','--dedupe-key',key,
         '--hypothesis',f'stitch18 integrator (LOO / near-tie / size-complementary composites at 27,400 B): price {genes} on main {base}',
         '--status',st,'--data',json.dumps(data)]
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode==0:
        open(OUT+'/res/recorded.txt','a').write(n+'\n')
    else: print('ledger fail',n,p.stderr[-300:])
print('ok')
