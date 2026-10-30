#!/usr/bin/env python3
"""rec.py <name> <hypothesis> [status]: record results.txt row <name> into the ledger."""
import sys,json,subprocess
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a48-cto-vaultspill'
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a48-cto-vaultspill'
name,hyp=sys.argv[1:3]; st=sys.argv[3] if len(sys.argv)>3 else None
row=[l for l in open(O+'/results.txt') if l.split(' ',1)[0]==name][-1]
js=row.split(' ',1)[1]; d=json.loads(js[:js.index('}')+1]); fb=js[js.index('}')+1:].strip()
if st is None: st='compile-failed' if not d['ok'] else ('rejected' if (d['ratio'] or 0)<=0.62103 else 'partial')
note=f"measure.sh on main 52c0b08 (0.62103): {d['bytes']} B ratio {d['ratio']} slots {d['slots']}; fbsplit {fb}" if d['ok'] else 'compile failed: '+d['err'][-150:]
data={'output':O+'/t/'+name,'normalized':d['n'],'raw':d['raw'],'losses':d['losses'],'raw_losses':d['rl'],'target':{'ratio':d['ratio'],'slots_diff':d['slots'],'cand_bytes':d['bytes']},'notes':note}
subprocess.run(['python3',WT+'/reconstruction/pump-main/log_attempt.py','record','--lane','w13a48-cto-vaultspill','--approach','source-variant','--target','0x22a10','--dedupe-key',f'0x22a10-w13-52c0b08-vaultspill-{name}-v1','--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],check=True)
