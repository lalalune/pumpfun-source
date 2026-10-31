#!/usr/bin/env python3
"""rec.py results.jsonl hyp.json : record each row in the shared ledger"""
import sys,json,subprocess
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a67-cto-h7src/reconstruction/pump-main/log_attempt.py'
H=json.load(open(sys.argv[2]))
for l in open(sys.argv[1]):
    l=l.strip()
    if not l or l=='DONE': continue
    parts=l.replace('} {','}\n{').split('\n'); r=json.loads(parts[0]); p=json.loads(parts[1]) if len(parts)>1 else {}
    n=r['name']
    if n not in H: continue
    key=f'0x22a10-w14-2e1379d-h7src-{n}-v1'
    if subprocess.run(['python3',L,'check','--dedupe-key',key],capture_output=True,text=True).returncode!=0: print('dup',key); continue
    st='compile-failed' if 'error' in r else ('analyzed' if r.get('ratio')==0.65728 and r.get('bytes')==27400 else 'rejected')
    note=f"raw-IR capture + rx opt/llc oracle on main 2e1379d (eq_main verified, 0.65728 fm 0.70431 sk 0.7885): ratio {r.get('ratio')} bytes {r.get('bytes')} fm {p.get('fm')} sk {p.get('sk')} err {p.get('err')}"+(' (= main tokens)' if st=='analyzed' else '')
    d={'output':'oracle','normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes')},'notes':note}
    x=subprocess.run(['python3',L,'record','--lane','w14a67-cto-h7src','--approach','h7src','--target','0x22a10','--dedupe-key',key,'--hypothesis',H[n],'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
    print(n,st,x.returncode,x.stderr[-200:])
