#!/usr/bin/env python3
"""rec3.py <res.txt> <lcs-file> <desc-json>: record new res lines (run1.sh format) in the ledger"""
import sys,os,re,subprocess,json
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a09-cto-tuplelocals/reconstruction/pump-main/log_attempt.py'
B=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
done_f=sys.argv[1]+'.recorded'; done=set(open(done_f).read().split()) if os.path.exists(done_f) else set()
lcs={}
for l in open(sys.argv[2]):
    p=l.split()
    if len(p)>2: lcs[p[0]]=p[-1]
desc=json.load(open(sys.argv[3]))
for l in open(sys.argv[1]):
    n,g=l.split()[:2]
    if n in done or n=='none': continue
    key=f'0x22a10-w15-{B}-tuplelocals-{n}-v1'
    if 'COMPILE FAIL' in l:
        st='compile-failed'; tgt={}; note='compile failed'
    else:
        m=re.search(r'B (\d+) M (\d+) fM (\d+) rM (\d+) rfM (\d+) rfjM (\d+)',l); j=json.loads(l.split(' | ')[2])
        tgt={'ratio':j['ratio'],'slots_diff':j.get('slots_diff'),'cand_bytes':j['bytes']}
        st='rejected' if not j.get('eq_main') else 'analyzed'
        note=f"raw-IR capture+opt+llc oracle on main {B}: B {m[1]} M {m[2]} fM {m[3]} rfM {m[5]} rfjM {m[6]} true-LCS {lcs.get(n)} (main M 2248 rfjM 2810 LCS rfj:3007); eq_main {j.get('eq_main')}"
    data={'output':f'rx/{n} (oracle, no full build)','normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':tgt,'notes':note}
    r=subprocess.run(['python3',L,'record','--lane','w15a09-cto-tuplelocals','--approach','tuplelocals','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f'tuplelocals per-field respelling {n}: {desc.get(n,g)}','--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
    if r.returncode: print('FAIL',key,r.stderr[-300:]); continue
    open(done_f,'a').write(n+'\n'); print('recorded',key,tgt.get('ratio'))
