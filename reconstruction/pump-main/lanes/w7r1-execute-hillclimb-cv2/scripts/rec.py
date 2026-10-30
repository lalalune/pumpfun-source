#!/usr/bin/env python3
"""rec.py PREFIX BASESHA BASERATIO DESC: record all results.jsonl rows with name PREFIX-* into the ledger (once)."""
import sys,json,subprocess,os
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-hillclimb-cv2')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w7r1-execute-hillclimb-cv2'
L=WT+'/reconstruction/pump-main/log_attempt.py'
prefix,bsha,bratio,desc=sys.argv[1:5]; bratio=float(bratio)
done=set(open(OUT+'/recorded.txt').read().split()) if os.path.exists(OUT+'/recorded.txt') else set()
sys.path.insert(0,OUT+'/scripts'); import muts
rows={}
for l in open(OUT+'/results.jsonl'):
    r=json.loads(l)
    if r['name'].startswith(prefix+'-'): rows[r['name']]=r
for n,r in rows.items():
    if n in done: continue
    mut=n[len(prefix)+1:]
    key=f'0x1e7c0-main-2b85821-hc-{mut}-on-{desc}-v1'
    if not r.get('ok'): st='compile-failed'; note='compile error: '+str(r.get('error'))[:200]
    elif r['sha']==bsha: st='rejected'; note=f'byte-identical to {desc} base ({bratio})'
    elif r['ratio']>bratio: st='partial' if r.get('losses')==[] and r.get('rlosses')==[] else 'built'; note=f"{bratio}->{r['ratio']} {r['bytes']} B sha {r['sha']}"+(f" N={r.get('N')} R={r.get('R')} losses={r.get('losses')} rlosses={r.get('rlosses')}" if 'N' in r else ' (unscored)')
    else: st='rejected'; note=f"{bratio}->{r['ratio']} {r['bytes']} B sha {r['sha']}"
    hyp=f"hill-climb mutation '{mut}' applied to {desc}: "+' ; '.join(f'{o[:70]!r}->{w[:70]!r}' if o!='FUNC' else str(w) for o,w in muts.M.get(mut.split('+')[0],[('?','?')]))[:600]
    data={'output':f'{OUT}/trials/{n}','target':{'ratio':r.get('ratio'),'cand_bytes':r.get('bytes')},'notes':note}
    p=subprocess.run(['python3',L,'record','--lane','w7r1-execute-hillclimb-cv2','--approach','mutation-hillclimb','--target','0x1e7c0','--dedupe-key',key,'--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
    print(n,st,note[:80],p.stdout.strip()[-60:])
    with open(OUT+'/recorded.txt','a') as f: f.write(n+'\n')
