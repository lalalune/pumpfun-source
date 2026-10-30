#!/usr/bin/env python3
# recall.py: record every res.jsonl row not yet recorded (rec.done) into the shared ledger
import json,os,subprocess
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a08-cto-outlinefill'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a08-cto-outlinefill/reconstruction/pump-main/log_attempt.py'
done=set(open(O+'/rec.done').read().split()) if os.path.exists(O+'/rec.done') else set()
for l in open(O+'/res.jsonl'):
    r=json.loads(l); n=r['name']
    if n in done or n=='rar0': continue
    w=r.get('1:2'); u=r.get('none')
    if not isinstance(w,dict): st='compile-failed'; tgt={}
    else:
        k=sum(1 for _ in open(f"{O}/bw/{n}_12/fn.txt")); M=round(w['ratio']*(3339+k)/2)
        st='rejected' if M<=2117 else 'partial'; tgt={'ratio':w['ratio'],'cand_bytes':w['bytes'],'matched_insns':M,'masked':w['masked']}
    note=f"raw-IR oracle on main cef0574 (0.63421@27400, M=2117 matched orig insns). w12=1:2 Some:None weights on validate 306 switch (outline stand-in). none={json.dumps(u)}; w12={json.dumps(w)}. RAR+w12 ref M=2099@26920. M>2117 needed to beat main at the pin."
    k=f"0x22a10-w14-cef0574-outlinefill-{n}-v1"
    subprocess.run(['python3',L,'record','--lane','w14a08-cto-outlinefill','--approach','outlinefill','--target','0x22a10','--dedupe-key',k,'--hypothesis',f"outline-basin fill screen: genes {'+'.join(r['genes'])} under 1:2 weights",'--status',st,'--data',json.dumps({'output':O+'/bw','target':tgt,'notes':note})],check=True,capture_output=True)
    done.add(n)
open(O+'/rec.done','w').write('\n'.join(sorted(done)))
print(len(done),'recorded')
