#!/usr/bin/env python3
"""rec.py <res.jsonl> [base_M base_bytes]: record every row in the shared ledger (dedupe by key; skips existing)."""
import sys,json,subprocess,os
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a31-cto-knob8')
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a31-cto-knob8/reconstruction/pump-main/log_attempt.py'
SHA=os.environ.get('SHA7','f100a59'); BM=int(os.environ.get('BM','2144')); BR=float(os.environ.get('BR','0.6423'))
done=set()
if os.path.exists(OUT+'/recorded.txt'): done=set(open(OUT+'/recorded.txt').read().split())
for l in open(sys.argv[1]):
    r=json.loads(l); n=r['name']; k=f'0x22a10-w14-{SHA}-knob8-{n}-v1'
    if k in done: continue
    try: ed=open(f'{OUT}/e/{n}.py').read()
    except OSError: ed=''
    if 'error' in r: st='compile-failed'; note='compile error'
    else:
        ident=r['M']==BM and r['bytes']==27400 and r['ratio']==BR
        st='analyzed' if ident else ('partial' if (r['bytes']==27400 and r['ratio']>BR) else 'rejected' if r['bytes']==27400 else 'analyzed')
        note=f"{r['bytes']} B ({r['bytes']-27400:+d}), M {r['M']} ({r['M']-BM:+d}), ratio {r['ratio']}"+(' (= main tokens)' if ident else '')
    d={'output':'raw-IR capture + rx oracle (w14a03 capvar/rx, M = matched tokens)','target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes'),'M':r.get('M')},'notes':f'size-knob screen on main {SHA} (0.6423, M {BM}). '+note+' edits: '+ed[-700:]}
    hyp=f'size knob {n} (tail/event/wallet/sweep spelling)'
    p=subprocess.run(['python3',L,'record','--lane','w14a31-cto-knob8','--approach','sizeknob','--target','0x22a10','--dedupe-key',k,'--hypothesis',hyp,'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
    if p.returncode==0: open(OUT+'/recorded.txt','a').write(k+'\n')
    else: print('fail',n,p.stderr[-200:])
print('ok')
