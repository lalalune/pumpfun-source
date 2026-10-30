#!/usr/bin/env python3
"""recb.py: ledger rows (approach slotpin) for each base from bound.jsonl (colour-level) + bound2.jsonl (interval-level)"""
import json,subprocess,os
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a18-cto-slotpin/reconstruction/pump-main/log_attempt.py'
B1={}; B2={}
for l in open(O+'/bound.jsonl'): r=json.loads(l); B1[r['tag']]=r
for l in open(O+'/bound2.jsonl'): r=json.loads(l); B2[r['tag']]=r
G={}
for l in open(O+'/res.jsonl'):
    r=json.loads(l); G[r['name']]=r.get('genes')
done=set(open(O+'/rec.done').read().split()) if os.path.exists(O+'/rec.done') else set()
for tag,r2 in B2.items():
    if tag in done: continue
    r1=B1.get(tag,{}); name=tag.rsplit('_',1)[0]; w=tag.rsplit('_',1)[1]; base='f8dc901' if tag.startswith('k_') else 'cef0574'
    key=f"0x22a10-w14-{base}-slotpin-{name}-{w}-v1"
    hyp=f"MIR slot-pin bound for base {name} (genes {G.get(name)}, weights {w}) on main {base}: colour-level pin (stop-before=prologepilog, fixed objects) and interval-level valid pin (stop-before=stack-slot-coloring, liveness-checked sharing) to the original's slots"
    data=dict(output=f"{O}/q/{tag}",target=dict(ratio=r2['ratio'],cand_bytes=r1.get('bytes'),M=r2['M']),
      notes=f"raw M {r2['M']}, frame-masked M {r1.get('maskedM')}; colour pin orig spill/all M {r1.get('b_spill_M')}/{r1.get('b_all_M')}; interval pin orig {r2.get('i_orig')} M {r2.get('i_orig_M')}; base pinned to main's frame M {r2.get('i_main_M')}; calibrated {r2['calibrated']} (identity pin = real build byte for byte)")
    subprocess.run(['python3',L,'record','--lane','w14a18-cto-slotpin','--approach','slotpin','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status','analyzed','--data',json.dumps(data)],check=True,capture_output=True)
    open(O+'/rec.done','a').write(tag+'\n'); print('recorded',key)
