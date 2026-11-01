#!/usr/bin/env python3
"""recstk.py <stkdir>...: record stacked-bound rows (stk.sh output) in the shared ledger (approach faithunion)."""
import sys,json,subprocess,os
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a09-cto-faithunion/reconstruction/pump-main/log_attempt.py'
for d in sys.argv[1:]:
    r=json.load(open(d+'/stk.json')); r.setdefault('stacked',max(r.get('Mfnhc',0),r.get('Mfnhc_plain',0))); tag=os.path.basename(d.rstrip('/'))
    key=f'0x22a10-w16-9bd38c7-fu-stk-{tag}-v1'
    if subprocess.run(['python3',L,'check','--dedupe-key',key],capture_output=True,text=True).returncode!=0:
        print('exists',key); continue
    note=(f"stacked bound (stk.sh: llc{' + '+str(r['nforce'])+' sticky RA forces' if r['nforce'] else ''}, layout restore = best of plain / blkrestore to main order, "
          f"fnorm alloca rebase to main frame + spill bestperm/swap climb): bytes {r['bytes']} M {r['M_plain']} Mfn {r['Mfn_plain']} stacked {r['stacked']} "
          f"(main unforced Mhc 2300, main p2 joint 2338); Lrfj {r['Lrfj_plain']} head {r['head_rfj']}; restore: {r['restore']}; forces {r['force'][:200]}")
    data={'output':d,'target':{'cand_bytes':r['bytes'],'M':r['M_plain'],'Mfn':r['Mfn_plain'],'stacked':r['stacked'],'Lrfj':r['Lrfj_plain'],'head_rfj':r['head_rfj'],'nforce':r['nforce']},'notes':note}
    p=subprocess.run(['python3',L,'record','--lane','w16a09-cto-faithunion','--approach','faithunion','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f"faithunion stacked bound (layout restore, frame normalisation, RA forces) for union {r['n']}",'--status','analyzed','--data',json.dumps(data)],capture_output=True,text=True)
    print(key,p.returncode,p.stderr[-200:])
