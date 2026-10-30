#!/usr/bin/env python3
"""rec.py <results.jsonl> <main7> <base_ratio>: write ledger rows for each IR-oracle result."""
import json,sys,subprocess,runpy
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a34-cto-newknobs'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a34-cto-newknobs/reconstruction/pump-main/log_attempt.py'
R,m7,br=sys.argv[1],sys.argv[2],float(sys.argv[3])
for l in open(R):
    r=json.loads(l); n=r['name']
    if n.startswith('base'): continue
    try: E=runpy.run_path(f'{O}/edits/{n}.py')['EDITS']
    except Exception: E=[]
    desc='; '.join(f'{a[:70]!r} -> {b[:90]!r}' for a,b in E)[:600]
    key=f'0x22a10-w13-{m7}-newknobs-{n}-v1'
    if subprocess.run(['python3',L,'check','--dedupe-key',key],capture_output=True).returncode!=0: continue
    st='compile-failed' if r.get('error')=='compile' else 'analyzed'
    d={'output':f'{O}/rx/{n}','normalized':None,'raw':None,'losses':[],'raw_losses':[],
       'target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes')},
       'notes':f"raw-IR opt+llc oracle (w13a23 rx.py) on main {m7} (base {br}); delta_bytes={r.get('bytes',27400)-27400} delta_ratio={round(r.get('ratio',br)-br,5)}; edit: {desc}"}
    subprocess.run(['python3',L,'record','--lane','w13a34-cto-newknobs','--approach','size-knob-screen','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f'new size knob {n}: semantics-preserving spelling outside frame/validate regions, screened with the raw-IR oracle','--status',st,'--data',json.dumps(d)],capture_output=True)
print('ok')
