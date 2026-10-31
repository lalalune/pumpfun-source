#!/usr/bin/env python3
"""rec2.py <results.txt>: record each new two.sh line (variant on main and on base O) in the ledger; hypothesis from og.D"""
import sys,os,re,subprocess,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import og
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a126-cto-origfill/reconstruction/pump-main/log_attempt.py'
B=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
df=sys.argv[1]+'.recorded'; done=set(open(df).read().split()) if os.path.exists(df) else set()
for l in open(sys.argv[1]):
    n,g=l.split()[:2]
    if n in done: continue
    fails='COMPILE FAIL' in l
    rows=re.findall(r'(\S+)\s+B (\d+) M (\d+) fM (\d+) rM (\d+) rfM (\d+) rfjM (\d+)',l)
    rat=re.findall(r'"name": "([^"]+)", "ratio": ([\d.]+)',l)
    note='; '.join(f'{a}: {b} B M {c} fM {d} rM {e} rfM {f} rfjM {h}' for a,b,c,d,e,f,h in rows)
    tgt={'ratio':float(rat[0][1]),'slots_diff':None,'cand_bytes':int(rows[0][1])} if rows else {}
    data={'output':f'$OUT/rx/{n} (raw-IR capture+opt+llc oracle)','normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':tgt,
          'notes':f'main {B} M 2247 rfjM 2810; base O (307/312 to_string noinline) M 1953 rfjM 2790. {note}'+(' COMPILE FAIL' if fails else '')}
    key=f'0x22a10-w14-{B}-origfill-{n}-v1'
    r=subprocess.run(['python3',L,'record','--lane','w14a126-cto-origfill','--approach','origfill','--target','0x22a10','--dedupe-key',key,
        '--hypothesis',f'origfill: {og.D.get(n,g)}','--status','compile-failed' if fails else 'rejected','--data',json.dumps(data)],capture_output=True,text=True)
    if r.returncode: print(r.stderr[-300:]); continue
    open(df,'a').write(n+'\n'); print('recorded',key)
