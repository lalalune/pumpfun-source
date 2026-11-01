#!/usr/bin/env python3
"""rec.py <name> <ids comma> <kind>: record a screened base in the shared ledger (one row per base). Experiment only."""
import sys,os,json,subprocess,collections
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a33-shim-drift'
LG=WT+'/reconstruction/pump-main/log_attempt.py'
R=json.load(open(OUT+'/res/ref.json'))
name,ids,kind=sys.argv[1],sys.argv[2],sys.argv[3]
rows=[json.loads(l) for l in open(OUT+f'/b/{name}.jsonl')]
c=collections.Counter(); best=None; bestoff=None; neu=set(); add=0; nadd=0; pos=0
for r in rows:
    if 'M' not in r: c['err']+=1; continue
    c['ok']+=1
    if r['bytes']==27400:
        if best is None or r['M']>best[0]: best=(r['M'],r['id'].split('+')[-1])
        if r['M']==2295: neu.add(r['sig'])
    elif bestoff is None or r['M']>bestoff[0]: bestoff=(r['M'],r['bytes'],r['id'].split('+')[-1])
    b=r['id'].split('+')[-1]
    if b in R:
        dm=R[b][0]
        if r['M']-2295==dm: add+=1
        else:
            nadd+=1
            if r['M']-2295>dm: pos+=1
hyp=(f"Neutral-drift harvest ({kind}): base {ids} (M 2295 = main, byte-changing) x the union of single-edit generators "
     f"(ptgen/anngen/vgen/gen/asgen: every main signature of code-changing cells within 16 B of the pinned size plus all edits within 15 IR lines of the base cells)")
note=(f"{c['ok']} combos screened ({c['err']} conflicts); best at 27400 B: M {best[0] if best else '-'} ({best[1] if best else '-'}); "
      f"main 2295; best off-size {bestoff}; {max(0,len(neu-{'61dcfe87f489'})-1)} distinct new neutral signatures at 27400; additivity vs main: {add} same dM, {nadd} different ({pos} better, all collapses)")
st='rejected' if (best is None or best[0]<=2295) else 'partial'
data={'output':OUT+f'/b/{name}.jsonl','target':{'ratio':round(2*best[0]/(3339+3337),5) if best else None,'cand_bytes':27400},'notes':note}
key=f'0x22a10-w17-8bee075-drift-base-{name}-v1'
r=subprocess.run(['python3',LG,'record','--lane','w17a33-shim-drift','--approach','drift','--target','0x22a10','--dedupe-key',key,
                  '--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
print(key,st,note[:200],r.stdout.strip()[-80:],r.stderr.strip()[-200:])
