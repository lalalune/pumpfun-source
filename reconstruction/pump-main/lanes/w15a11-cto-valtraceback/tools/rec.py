#!/usr/bin/env python3
"""rec.py <name>...: record oracle trials in the shared ledger with true-LCS stats."""
import sys,os,json,subprocess
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a11-cto-valtraceback'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a11-cto-valtraceback/reconstruction/pump-main/log_attempt.py'
ev=subprocess.run(['python3',O+'/t2/ev.py',*sys.argv[1:]],capture_output=True,text=True).stdout.splitlines()
evd={l.split()[0]:l for l in ev[1:]}
for n in sys.argv[1:]:
    key=f'0x22a10-w15-90300f9-valtraceback-{n}-v1'
    eds=json.load(open(f'{O}/e/{n}.py'.replace('.py','.py'))) if False else open(f'{O}/e/{n}.py').read()[6:].strip()
    try: res=json.load(open(f'{O}/rx/{n}/res.json'))
    except Exception: res={'error':'compile'}
    eq=res.get('eq_main'); st='rejected' if not res.get('ratio') or res['ratio']<=0.67346 else 'built'
    note=f"raw-IR capture+opt+llc oracle on main 90300f9 (m0 eq_main, 0.67346 @27400, true-LCS ---2253 rfj3007): {evd.get(n,'compile-failed')}; byte-identical to main" if eq else f"raw-IR capture+opt+llc oracle on main 90300f9 (m0 eq_main, 0.67346 @27400, true-LCS ---2253 rfj3007): {evd.get(n,'compile-failed')}"
    data={'output':f'{O}/rx/{n}','target':{'ratio':res.get('ratio'),'slots_diff':res.get('slots_diff'),'cand_bytes':res.get('bytes')},'notes':note}
    r=subprocess.run(['python3',L,'record','--lane','w15a11-cto-valtraceback','--approach','valtraceback','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f'valtraceback validate idiom {n}: EDITS={eds[:600]}','--status',st if 'error' not in res else 'compile-failed','--data',json.dumps(data)],capture_output=True,text=True)
    print(n,(r.stdout+r.stderr).strip()[-120:])
