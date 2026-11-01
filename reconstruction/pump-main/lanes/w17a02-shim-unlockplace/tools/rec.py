#!/usr/bin/env python3
# rec.py <name> <hypothesis> [notes]: record a measured trial (res/<name>.json) in the shared ledger
import sys,json,subprocess,os
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a02-shim-unlockplace'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a02-shim-unlockplace/reconstruction/pump-main/log_attempt.py'
n,h=sys.argv[1],sys.argv[2]; notes=sys.argv[3] if len(sys.argv)>3 else ''
d=json.loads(open(f'{OUT}/res/{n}.json').read())
key=f'0x22a10-w17-5998913-shimunlock-{n}-v1'
if not d.get('ok'):
    st='compile-failed'; data={'output':d.get('out',''),'notes':notes+' '+str(d.get('error',''))[-300:]}
else:
    c=d['admin_cto']; better=c['cand_bytes']==27400 and c['ratio']>0.67436 and not d['losses'] and not d['raw_losses']
    st='built' if not better else 'partial'
    data={'output':d['out'],'normalized':d['normalized'],'raw':d['raw'],'losses':d['losses'],'raw_losses':d['raw_losses'],
          'target':{'ratio':c['ratio'],'slots_diff':c['slots_diff'],'cand_bytes':c['cand_bytes']},'notes':notes}
r=subprocess.run(['python3',L,'record','--lane','w17a02-shim-unlockplace','--approach','shimunlock','--target','0x22a10','--dedupe-key',key,
  '--hypothesis',h,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
print(r.returncode,(r.stdout+r.stderr)[-200:])
