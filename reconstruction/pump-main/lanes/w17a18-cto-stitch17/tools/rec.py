#!/usr/bin/env python3
"""rec.py: record every res/cap.jsonl row not yet recorded into the shared ledger (approach stitch17)."""
import sys,os,json,subprocess
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T)
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a18-cto-stitch17'
L=WT+'/reconstruction/pump-main/log_attempt.py'
done=set(open(OUT+'/res/recorded.txt').read().split()) if os.path.exists(OUT+'/res/recorded.txt') else set()
MAIN=(2270,27400)
for l in open(OUT+'/res/cap.jsonl'):
    r=json.loads(l); n=r['name']
    if n in done: continue
    key=f'0x22a10-w17-bf01b5f-stitch17-{n}-v1'
    genes='+'.join(r.get('genes',[])) or 'main'
    if 'err' in r:
        st='compile-failed'; data={'output':f'{OUT}/fx/{n}','notes':f"genes {genes}: {r['err']} {r.get('detail','')}"[:500]}
    else:
        st='analyzed'
        data={'output':f'{OUT}/fx/{n}','target':{'ratio':r['ratio'],'slots_diff':r.get('slots'),'cand_bytes':r['bytes']},
              'notes':f"slim pre-opt oracle (capraw+preslim+fx) on main bf01b5f (oracle M 2270 @27400, slots 3169): genes {genes} -> M {r['M']} @{r['bytes']} (dM {r['M']-2270:+d}, dB {r['bytes']-27400:+d}), oracle slots {r.get('slots')}"}
    cmd=['python3',L,'record','--lane','w17a18-cto-stitch17','--approach','stitch17','--target','0x22a10','--dedupe-key',key,
         '--hypothesis',f'stitch17 integrator: price {genes} on the shim-era main bf01b5f (size-complementary composites at 27,400 B)',
         '--status',st,'--data',json.dumps(data)]
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode==0:
        open(OUT+'/res/recorded.txt','a').write(n+'\n')
    else: print('ledger fail',n,p.stderr[-300:])
print('ok')
