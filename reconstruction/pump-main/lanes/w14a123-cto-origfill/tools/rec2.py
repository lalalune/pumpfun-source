#!/usr/bin/env python3
"""rec2.py <res.txt> <note>: record each new line (plain + _O on base O = 307/312 call-site noinline) in the ledger"""
import sys,os,re,subprocess,json
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a123-cto-origfill/reconstruction/pump-main/log_attempt.py'
B=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
done_f=sys.argv[1]+'.recorded'; done=set(open(done_f).read().split()) if os.path.exists(done_f) else set()
for l in open(sys.argv[1]):
    m=re.match(r'(\S+) (\S+) \| (.*)',l)
    if not m: continue
    n,g,rest=m.groups()
    if n in done: continue
    v=re.findall(r'(\S+)\s+B (\d+) M (\d+) fM (\d+) rM (\d+) rfM (\d+) rfjM (\d+)',rest)
    if len(v)<1: st='compile-failed'; tgt={'ratio':None,'slots_diff':None,'cand_bytes':None}; extra=rest[:300]
    else:
        st='rejected'; _,b,M,fM,rM,rfM,rfjM=v[0]; r=2*int(M)/(3337+int(b)//8) if False else None
        tgt={'ratio':None,'slots_diff':None,'cand_bytes':int(b)}
        extra='; '.join(f'{x[0]}: B {x[1]} M {x[2]} fM {x[3]} rM {x[4]} rfM {x[5]} rfjM {x[6]}' for x in v)
    key=f'0x22a10-w14-{B}-origfill-{n}-v1'
    data={'output':f'rx/{n} (raw-IR capture+opt+llc oracle, no full build)','normalized':None,'raw':None,'losses':[],'raw_losses':[],
          'target':tgt,'notes':f'origfill raw-IR oracle on main {B} (main B 27400 M 2247 rfjM 2810; base O = main + 307/312 to_string call-site noinline: B 26992 M 1953 rfjM 2790): genes {g}; {extra}; {sys.argv[2]}'}
    subprocess.run(['python3',L,'record','--lane','w14a123-cto-origfill','--approach','origfill','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f'origfill screen on main and on base O: {g}','--status',st,'--data',json.dumps(data)],capture_output=True)
    open(done_f,'a').write(n+'\n'); print('recorded',key)
