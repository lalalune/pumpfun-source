#!/usr/bin/env python3
"""rec.py <res.jsonl> <hyp-prefix>: record oracle rows in the shared ledger (w14a34-cto-curvetail)."""
import sys,json,subprocess,os
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a34-cto-curvetail/reconstruction/pump-main/log_attempt.py'
MAIN=os.environ.get('MAIN','5ee681d'); BASE=float(os.environ.get('BASE','0.645'))
res,pre=sys.argv[1],sys.argv[2]
D=os.path.dirname(os.path.abspath(__file__))
for l in open(res):
    d=json.loads(l); n=d['name']
    ed=open(f'{D}/e/{n}.py').read()[:600]
    r=d.get('ratio')
    st='compile-failed' if d.get('error') else ('rejected' if (r is None or r<=BASE) else 'partial')
    note=f"raw-IR capture + rx opt/llc oracle (= build tokens; m0 reproduces measure.sh build of main) on main {MAIN} ({BASE} @27400): ratio {r} bytes {d.get('bytes')} slots {d.get('slots_diff')}. edits: {ed}"
    data={'output':f'~/.cache/pumpfun-reconstruction/lanes/w14a34-cto-curvetail/rx/{n}','target':{'ratio':r,'slots_diff':d.get('slots_diff'),'cand_bytes':d.get('bytes')},'notes':note}
    subprocess.run(['python3',L,'record','--lane','w14a34-cto-curvetail','--approach','curvetail','--target','0x22a10',
        '--dedupe-key',f'0x22a10-w14-{MAIN}-curvetail-{n}-v1','--hypothesis',f'{pre}: {n}','--status',st,'--data',json.dumps(data)],check=False,capture_output=True)
    print(n,st)
