#!/usr/bin/env python3
"""rec2.py <name>...: record c1b01frame oracle trials (ratio/bytes, true-LCS, Mperm/Mhc) in the shared ledger; writes grid.jsonl."""
import sys,os,json,subprocess
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a19-cto-c1b01frame'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a19-cto-c1b01frame/reconstruction/pump-main/log_attempt.py'
ev=subprocess.run(['python3',O+'/t2/evall.py',*sys.argv[1:]],capture_output=True,text=True).stdout.splitlines()
evd={l.split()[0]:l for l in ev[1:]}
G=open(O+'/grid.jsonl','a')
for n in sys.argv[1:]:
    key=f'0x22a10-w15-86e2a6b-c1b01frame-{n}-v1'
    eds=open(f'{O}/e/{n}.py').read()[6:].strip()
    try: res=json.load(open(f'{O}/rx/{n}/res.json'))
    except Exception: res={'error':'compile'}
    try: ph=json.load(open(f'{O}/rx/{n}/permhc.json'))
    except Exception: ph={}
    e=evd.get(n,'')
    row={'name':n,**res,'M':ph.get('M'),'Mperm':ph.get('Mperm'),'Mhc':ph.get('Mhc'),'ev':e}; G.write(json.dumps(row)+'\n')
    st='rejected' if not res.get('ratio') or res['ratio']<=0.67376 or res.get('bytes')!=27400 else 'built'
    if 'error' in res: st='compile-failed'
    note=(f"raw-IR capture+opt+llc oracle on main 86e2a6b (m0 eq_main 0.67376 @27400, M 2249 Mperm 2293 Mhc 2300, true-LCS ---2255 rfj3007): "
          f"M {ph.get('M')} Mperm {ph.get('Mperm')} Mhc {ph.get('Mhc')}; {e}"+("; byte-identical to main" if res.get('eq_main') else ""))
    data={'output':f'{O}/rx/{n}','target':{'ratio':res.get('ratio'),'slots_diff':res.get('slots_diff'),'cand_bytes':res.get('bytes')},'notes':note}
    r=subprocess.run(['python3',L,'record','--lane','w15a19-cto-c1b01frame','--approach','c1b01frame','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f'c1b01frame composite {n} (cash c1/c2/c5/c6 per-arm cashback x b01/b02 holder_key by value x g1/g3 early creator): EDITS={eds[:700]}','--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
    print(n,(r.stdout+r.stderr).strip()[-100:])
