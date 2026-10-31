#!/usr/bin/env python3
"""rec4.py <res.txt>: record new res lines (run1.sh format) in the ledger, approach creatorcopy; genes text from tg.G"""
import sys,os,re,subprocess,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import tg
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a21-cto-creatorcopy/reconstruction/pump-main/log_attempt.py'
B=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
done_f=sys.argv[1]+'.recorded'; done=set(open(done_f).read().split()) if os.path.exists(done_f) else set()
OUT=os.path.dirname(T)
for l in open(sys.argv[1]):
    n,g=l.split()[:2]
    if n in done or n=='none': continue
    key=f'0x22a10-w15-{B}-creatorcopy-{n}-v1'
    if 'COMPILE FAIL' in l:
        st='compile-failed'; tgt={}; note='compile failed'
    else:
        m=re.search(r'B (\d+) M (\d+) fM (\d+) rM (\d+) rfM (\d+) rfjM (\d+)',l); j=json.loads(l.split(' | ')[2])
        lc=subprocess.run(['python3',T+'/lcs.py',n,'--masks','---,rfj'],capture_output=True,text=True,cwd=OUT).stdout.split()
        tgt={'ratio':j['ratio'],'slots_diff':j.get('slots_diff'),'cand_bytes':j['bytes']}
        st='rejected' if not j.get('eq_main') else 'analyzed'
        note=f"raw-IR capture+opt+llc oracle on main {B}: B {m[1]} M {m[2]} rfjM {m[6]} true-LCS {' '.join(lc[2:])} (main 27400 B M 2249 rfjM 2809 LCS ---:2255 rfj:3007); eq_main {j.get('eq_main')}"
    eds=[]
    for gn in g.split('+'):
        eds+=tg.G.get(gn,[])
    desc='; '.join(f'{a[:70]!r}->{b[:110]!r}' for a,b in eds)[:900]
    data={'output':f'rx/{n} (oracle, no full build)','normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':tgt,'notes':note}
    r=subprocess.run(['python3',L,'record','--lane','w15a21-cto-creatorcopy','--approach','creatorcopy','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f'creatorcopy {n} ({g}): {desc}','--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
    if r.returncode: print('FAIL',key,r.stderr[-300:]); continue
    open(done_f,'a').write(n+'\n'); print('recorded',key,tgt.get('ratio'))
