#!/usr/bin/env python3
"""rec.py [names...]: record res.jsonl rows (raw-IR oracle) in the shared ledger, once per name (rec.done)."""
import json,os,subprocess,sys
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a07-cto-sweeptuple'
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a07-cto-sweeptuple'
L=WT+'/reconstruction/pump-main/log_attempt.py'
SHA=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
DESC={'A1':'AMM guard as `match amm_frozen as i32{1=>660,_=>if !empty{TCF}}`','A2':'AMM guard `match amm_frozen as i32{0=>if !empty{TCF},_=>660}`',
 'A3':'AMM guard tuple `match (amm_present,amm_frozen){(true,true)=>660,(true,false)=>TCF,(false,_)=>{}}` (drops 2nd data_is_empty)',
 'A5':'AMM guard sibling tuple `match (amm_present,amm_frozen){(true,true)=>660,(_,false)=>if !empty{TCF},(false,true)=>{}}`',
 'A6':'AMM tuple with TCF arm first `(_,false)=>if !empty{TCF},(true,true)=>660,(false,true)=>{}`','A7':'AMM tuple `(false,_)=>{}` first then (true,true)=>660,(true,false)=>TCF',
 'N1':'vault arms `match native as i32{1=>native,_=>token}`','N2':'vault arms `match native as i32{0=>token,_=>native}` (native arm moved to line 721)',
 'T1':'token arm `match (frozen,amount>0){(true,_)=>719,(false,true)=>CPI,(false,false)=>{}}`','T2':'token arm `match frozen as i32{1=>719,_=>if amount>0{CPI}}`',
 'T3':'token arm tuple with CPI arm first','T4':'token arm `match (amount>0,frozen){(true,false)=>CPI,(_,true)=>719,(false,false)=>{}}`','T5':'token arm `match (frozen,amount){(false,0)=>{},(true,_)=>719,(false,_)=>CPI}`',
 'V1':'native amount `match (amount>0) as i32{1=>..,_=>Ok(())}`','a1':'token arm amount-first (orig call order)','t1':'a1 + separate ? on create_idempotent and transfer_vault_tokens (w14a70 t1)',
 'A6b':'AMM `match (amm_frozen,amm_present){(false,_)=>if !empty{TCF},(true,true)=>660,(true,false)=>{}}`','A6c':'AMM `match amm_frozen{false=>if !empty{TCF},true=>660}`','A6d':'AMM `match (amm_present,amm_frozen){(_,false)=>if !empty{TCF},_=>660}`','A6e':'AMM `if !amm_frozen{if !empty{TCF}}else{660}`','P1':'660 `match token_raw_amount(..){Ok(v)=>require!(v==0),Err(e)=>return Err(e)}`','P2':'660 explicit match, Err arm first','P7':'660 `token_raw_amount(..).and_then(|v|{require!;Ok(())})?`','P8':'660 `require!(token_raw_amount(..).map(|v|v==0)?,..)`','0':'base only'}
BASE={'m':'main','s':'sh_iflet','t':'tai TCF program (w15a26 p_tai)'}
done=set(open(O+'/rec.done').read().split()) if os.path.exists(O+'/rec.done') else set()
want=set(sys.argv[1:])
import re
for l in open(O+'/res.jsonl'):
    d=json.loads(l); n=d['name']
    if n in done or (want and n not in want) or n=='m0': continue
    b,v=n.split('_',1); parts=re.findall(r'[A-Z][0-9][a-z]?|[a-z][0-9]|0',v)
    hyp=f"sweeptuple {n}: base {BASE[b]} + "+' + '.join(DESC.get(x,x) for x in parts)
    if 'error' in d:
        st='compile-failed'; note=d['error'][:300]
    else:
        st='analyzed'; note=f"raw-IR capture + rx opt/llc oracle on main {SHA} (m0 eq_main, 0.67376 M2249 Mperm2292 @27400): {d['bytes']} B ratio {d['ratio']} M {d['M']} Mperm {d['Mperm']} eq_main {d['eq_main']}; TCF first-clone regs {d['mk']} (orig lam r7 key r9 data r0 E r5 O r6; hits {d['mk_hits']}/5)"
    data={'output':O+'/rx/'+n,'normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':{'ratio':d.get('ratio'),'slots_diff':d.get('slots_diff'),'cand_bytes':d.get('bytes')},'notes':note}
    r=subprocess.run(['python3',L,'record','--lane','w16a07-cto-sweeptuple','--approach','sweeptuple','--target','0x22a10','--dedupe-key',f'0x22a10-w16-{SHA}-sweeptuple-{n}-v1','--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
    print(n,r.returncode,r.stdout.strip()[:120],r.stderr.strip()[:200])
    if r.returncode==0: open(O+'/rec.done','a').write(n+'\n')
