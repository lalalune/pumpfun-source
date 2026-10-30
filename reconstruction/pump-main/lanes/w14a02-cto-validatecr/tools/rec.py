#!/usr/bin/env python3
"""rec.py name [name..] : record trials in the shared ledger (analyzed, IR-capture oracle)."""
import sys,json,subprocess,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a02-cto-validatecr')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a02-cto-validatecr'
L=WT+'/reconstruction/pump-main/log_attempt.py'
R={};C={}
for l in open(O+'/results.jsonl'):
    try: d=json.loads(l); R[d['name']]=d
    except: pass
for l in open(O+'/chunks.jsonl'):
    try: d=json.loads(l); C[d['name']]=d
    except: pass
done=set(open(O+'/recorded.txt').read().split()) if os.path.exists(O+'/recorded.txt') else set()
for n in sys.argv[1:]:
    if n in done: continue
    r=R.get(n,{}); c=C.get(n,{})
    key='0x22a10-w14-23322b0-validatecr-%s-v1'%n
    hyp='validate clean-room composite on main 23322b0: genes %s (lane e/gen.py: v2=nested 289 holder threading (w13a43 T289N), ov=shared override in non-holder arm (w13a04 OVMK), h2=holder out-param phi (w13a38), anew=sharing arm Some(new) no args copy, lv3n=w13a45 out-param fee-None threading, smap=w13a31 token .map, hm=matches! holder, pda=PDA before shared)'%n.split('_')
    note='raw-IR capture + rx oracle (= build tokens). %s B, ratio %s (main 0.62882), fm %s rm %s (main 0.72169/0.84991), validate-chunk rm 0x0-0x1800 %s (main 429), rm total %s (main 2837), calls %s, chunks %s'%(c.get('bytes'),r.get('ratio'),c.get('fm'),c.get('rm'),c.get('rmV'),c.get('rmT'),c.get('calls'),c.get('rmC'))
    data={'output':O+'/rx/'+n,'target':{'ratio':r.get('ratio'),'slots_diff':None,'cand_bytes':c.get('bytes')},'notes':note}
    p=subprocess.run(['python3',L,'record','--lane','w14a02-cto-validatecr','--approach','validate-cleanroom-composite','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status','rejected' if (r.get('ratio') or 0)<0.62882 or c.get('bytes')!=27400 else 'partial','--data',json.dumps(data)],capture_output=True,text=True)
    print(n,p.returncode,p.stderr[-200:])
    if p.returncode==0: open(O+'/recorded.txt','a').write(n+'\n')
