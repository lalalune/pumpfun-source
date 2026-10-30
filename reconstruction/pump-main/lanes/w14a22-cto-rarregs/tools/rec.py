#!/usr/bin/env python3
# rec.py <res.jsonl> <sha7> <main_M> <desc-prefix>: ledger rows for oracle trials
import sys,json,subprocess
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a22-cto-rarregs/reconstruction/pump-main/log_attempt.py'
f,sha,mm,desc=sys.argv[1:5]; mm=int(mm)
for l in open(f):
    r=json.loads(l); x=r.get('none'); key=f"0x22a10-w14-{sha}-rarregs-{r['name']}-v1"
    if isinstance(x,dict):
        n=x['bytes']//8-x['lddw']; M=round(x['ratio']*(3339+n)/2)
        st='rejected' if M<=mm else 'partial'
        data={'target':{'ratio':x['ratio'],'cand_bytes':x['bytes']},'notes':f"oracle (raw-IR+opt+llc) M {M} vs main {mm}; outlined to_string {x['outl']}"}
    else:
        st='compile-failed'; data={'notes':str(r.get('err'))}
    subprocess.run(['python3',L,'record','--lane','w14a22-cto-rarregs','--approach','rarregs','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f"{desc}: genes {','.join(r['genes'])} on main {sha}",'--status',st,'--data',json.dumps(data)],capture_output=True)
    print(key,st)
