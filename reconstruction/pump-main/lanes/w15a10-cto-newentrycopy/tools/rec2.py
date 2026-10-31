#!/usr/bin/env python3
"""rec2.py <res.txt> <note>: record each new raw-IR oracle line of res.txt in the ledger"""
import sys,os,re,subprocess,json
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a10-cto-newentrycopy'
L=WT+'/reconstruction/pump-main/log_attempt.py'
B=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
df=sys.argv[1]+'.recorded'; done=set(open(df).read().split()) if os.path.exists(df) else set()
for l in open(sys.argv[1]):
    p=l.split(' | ')
    n,g=p[0].split()
    if n in done: continue
    if 'FAIL' in p[1]:
        st='compile-failed'; tgt={'ratio':None,'slots_diff':None,'cand_bytes':None}; extra=p[1][:300]
    else:
        r=json.loads(p[1]); tgt={'ratio':r['ratio'],'slots_diff':r.get('slots_diff'),'cand_bytes':r['bytes']}; extra=' | '.join(x.strip() for x in p[2:])
        st='rejected' if not r.get('eq_main') else 'analyzed'
    key=f'0x22a10-w15-{B}-newentrycopy-{n}-v1'
    data={'output':f'rx/{n} (raw-IR capture + opt + llc oracle)','normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':tgt,
          'notes':f'newentrycopy on main {B}: genes {g}; {extra}; {sys.argv[2]}'}
    subprocess.run(['python3',L,'record','--lane','w15a10-cto-newentrycopy','--approach','newentrycopy','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f'entry copy of new joint state: {g}','--status',st,'--data',json.dumps(data)],capture_output=True)
    open(df,'a').write(n+'\n'); print('recorded',key)
