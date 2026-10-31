#!/usr/bin/env python3
"""rec15.py <results.txt> [note-prefix]: record each new cap.sh line in the ledger (approach t312repay)."""
import sys,os,re,subprocess,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import g15
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a02-cto-t312repay/reconstruction/pump-main/log_attempt.py'
B=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
pre=sys.argv[2] if len(sys.argv)>2 else ''
df=sys.argv[1]+'.recorded'; done=set(open(df).read().split()) if os.path.exists(df) else set()
for l in open(sys.argv[1]):
    n,g=l.split()[:2]
    if n in done: continue
    fails='COMPILE FAIL' in l
    m=re.search(r'B (\d+) M (\d+) fM (\d+) rM (\d+) rfM (\d+) rfjM (\d+)',l); r=re.search(r'"ratio": ([0-9.]+)',l)
    o=re.search(r'(284[IO] .*?) orig',l); eq='"eq_main": true' in l
    note=f'T base = h307 is_zero + h312 invalid_creator helpers (w14a141). main {B} M 2248 rfjM 2810 @27400; T M 2199 @27184. '
    if m: note+=f'{n}: B {m.group(1)} M {m.group(2)} fM {m.group(3)} rM {m.group(4)} rfM {m.group(5)} rfjM {m.group(6)} ratio {r.group(1) if r else "?"} eq_main {eq}; outline {o.group(1) if o else "?"}. '
    note+=pre
    tgt={'ratio':float(r.group(1)),'slots_diff':None,'cand_bytes':int(m.group(1))} if (m and r) else {}
    eds=[]
    for x in g.split('+'):
        eds+= g15.G.get(x,[('see g141/og genes',x)]) if x in g15.G else [('gene',x)]
    data={'output':f'$OUT/rx/{n} (raw-IR capture+opt+llc oracle)','normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':tgt,'notes':note+(' COMPILE FAIL' if fails else '')}
    key=f'0x22a10-w15-{B}-t312repay-{n}-v1'
    hyp=f't312repay {g}: EDITS={json.dumps(eds)[:1500]}'
    rr=subprocess.run(['python3',L,'record','--lane','w15a02-cto-t312repay','--approach','t312repay','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',hyp,'--status','compile-failed' if fails else 'rejected','--data',json.dumps(data)],capture_output=True,text=True)
    if rr.returncode: print(rr.stderr[-300:]); continue
    open(df,'a').write(n+'\n'); print('recorded',key)
