#!/usr/bin/env python3
"""rec.py <results.txt> <mechanism note>: record each new line in the ledger (raw-IR oracle rows)"""
import sys,os,re,subprocess,json
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a108-cto-crlrepay/reconstruction/pump-main/log_attempt.py'
B=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
done_f=sys.argv[1]+'.recorded'; done=set(open(done_f).read().split()) if os.path.exists(done_f) else set()
for l in open(sys.argv[1]):
    m=re.match(r'(\S+) (\S+) \| \S+\s+bytes (\d+) M (\d+) ratio ([\d.]+) skM (\d+)',l)
    if not m: continue
    n,g,b,M,r,sk=m.groups()
    if n in done: continue
    key=f'0x22a10-w14-{B}-crlrepay-{n}-v1'
    data={'output':f'rx/{n} (raw-IR capture+opt+llc oracle, no full build)','normalized':None,'raw':None,'losses':[],'raw_losses':[],
          'target':{'ratio':float(r),'slots_diff':None,'cand_bytes':int(b)},'notes':f'crlrepay raw-IR oracle on main {B}: genes {g}; M {M} skM {sk}; {sys.argv[2]}'}
    subprocess.run(['python3',L,'record','--lane','w14a108-cto-crlrepay','--approach','crlrepay','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f'crl_L faithful size repay screen: {g} ({sys.argv[2]})','--status','rejected','--data',json.dumps(data)],capture_output=True)
    open(done_f,'a').write(n+'\n'); print('recorded',key)
