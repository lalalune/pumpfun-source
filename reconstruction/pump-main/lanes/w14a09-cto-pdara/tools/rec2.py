#!/usr/bin/env python3
"""rec2.py [names..|--all]: record pda-partner screen rows from results2.jsonl in the shared ledger."""
import sys,json,subprocess,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a09-cto-pdara')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a09-cto-pdara'
L=WT+'/reconstruction/pump-main/log_attempt.py'
R={}
RF=os.environ.get('RES',O+'/results2.jsonl'); SHA=os.environ.get('SHA','769f331'); MR=os.environ.get('MR','0.63241')
for l in open(RF):
    try: d=json.loads(l); R[d['name']]=d
    except: pass
DONEF=O+'/recorded_%s.txt'%SHA if SHA!='769f331' else O+'/recorded2.txt'
done=set(open(DONEF).read().split()) if os.path.exists(DONEF) else set()
names=list(R) if sys.argv[1:]==['--all'] else sys.argv[1:]
H={'nopda':'main baseline capture (no pda)','hHold':'hb=holder==Some(true) bound at entry before the PDA','hCb':'curve.is_cashback_coin read at entry before the PDA','hMay':'curve.is_mayhem_mode read at entry before the PDA','hHr':'curve.is_holder_reward read at entry','hHoldE':'holder via matches!','hL':'shared tests bonding_curve.creator on the left (original memcmp operand order)','hK1':'let holder_key=FPA(..).0','hK2':'let (holder_key,_)=FPA(..)','hSK':'sk=sharing_config.key() bound at entry before the PDA, used by shared','hSKp':'sk bound after the PDA, used by shared','hBC':'let bc=&a.bonding_curve before PDA','hIF':'shared as if key==creator{owner&&!empty}else{false}','hQL':'quote_locked before shared','hMint':'PDA seeds use a.mint.key() inline, mint bound after'}
for n in names:
    if n in done: continue
    r=R[n]
    key='0x22a10-w14-%s-pdara-%s-v1'%(SHA,n.replace('+','.'))
    genes=n.split('+')
    hyp='holder_key PDA before shared (pda, original call order) + partner(s) %s on main %s: %s'%(genes,SHA,'; '.join(H.get(g,'gene '+g+' (w13a47 genes47 g_* / sizeknobs-cto.json k_*)') for g in genes if g!='pda'))
    note='raw-IR capture + rx opt/llc oracle (= build tokens). %s B, ratio %s (main %s), rm %s rm0x0-0x1800 %s (main 432) rmT %s (main 2827); RA: %s'%(r.get('bytes'),r.get('ratio'),MR,r.get('rm'),r.get('rmV'),r.get('rmT'),(r.get('coal') or r.get('error') or '')[:110])
    st='compile-failed' if r.get('error') else ('rejected' if (r.get('ratio') or 0)<=float(MR) or r.get('bytes')!=27400 else 'partial')
    data={'output':O+'/rx/'+n.replace('+','_'),'target':{'ratio':r.get('ratio'),'slots_diff':None,'cand_bytes':r.get('bytes')},'notes':note}
    p=subprocess.run(['python3',L,'record','--lane','w14a09-cto-pdara','--approach','pda-first-ra-partner','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
    if p.returncode==0: open(DONEF,'a').write(n+'\n')
    else: print(n,p.returncode,p.stderr[-300:])
