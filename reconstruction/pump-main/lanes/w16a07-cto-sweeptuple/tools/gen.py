#!/usr/bin/env python3
"""gen.py: sweep decision respellings in the sibling idioms (tuple match, `as i32` match) x bases (m=main, s=sh_iflet,
t=tai TCF program). Writes e/<base>_<variant>.py with EDITS = base edits + one region edit (lines 647..726)."""
import os,runpy,sys
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a07-cto-sweeptuple'
E='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a07-cto-sweeptuple/e'
SRC=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
BASES={'m':[],
 's':[("\n match sharing_update{Some(val)=>{\n","\n if let Some(val)=sharing_update{{\n"),("\n }None=>{}}\n","\n }}\n")],
 't':runpy.run_path(E+'/base_tai.py')['EDITS']}
def app(s,ed):
    for a,b in ed:
        assert s.count(a)==1,(s.count(a),a[:80]); s=s.replace(a,b)
    return s
LO,HI=647,726
def parts(L):
    g=lambda n:L[n-1]
    P661='  else if !a.coin_creator_vault_ata.data_is_empty(){'
    assert g(661).startswith(P661) and g(661).endswith('}'); TCF=g(661)[len(P661):-1]
    P660='  if amm_frozen{'; assert g(660).startswith(P660) and g(660).endswith('}'); REQ660=g(660)[len(P660):-1]
    P663='  if native{'; assert g(663).startswith(P663); NAT_HEAD=g(663)[len(P663):]
    k=g(664).index('}else{let frozen='); NAT_TAIL=g(664)[:k]; TOK_HEAD=g(664)[k+len('}else{'):]
    P719='   if frozen{'; assert g(719).startswith(P719)
    k=g(719).index('}else if amount>0{'); REQ719=g(719)[len(P719):k]; TOKCPI=g(719)[k+len('}else if amount>0{'):-1]
    assert g(720)=='   Ok(amount)}' and g(721)=='' and g(659)=='' and g(726)==' }'
    return dict(TCF=TCF,REQ660=REQ660,NAT_HEAD=NAT_HEAD,NAT_TAIL=NAT_TAIL,TOK_HEAD=TOK_HEAD,REQ719=REQ719,TOKCPI=TOKCPI)
EMPTY='!a.coin_creator_vault_ata.data_is_empty()'
def V(name,L,p):
    s=lambda n,t:L.__setitem__(n-1,t)
    TCF,REQ660,NH,NT,TH,REQ719,TC=(p[k] for k in ('TCF','REQ660','NAT_HEAD','NAT_TAIL','TOK_HEAD','REQ719','TOKCPI'))
    for part in name.split('+'):
        if part=='A1': s(660,'  match amm_frozen as i32{1=>{'+REQ660+'}'); s(661,'  _=>if '+EMPTY+'{'+TCF+'}}')
        elif part=='A2': s(659,'  match amm_frozen as i32{0=>if '+EMPTY+'{'+TCF+'}'); s(660,'  _=>{'+REQ660+'}}'); s(661,'')
        elif part=='A3': s(660,'  match (amm_present,amm_frozen){(true,true)=>{'+REQ660+'}'); s(661,'  (true,false)=>{'+TCF+'}(false,_)=>{}}')
        elif part=='A5': s(660,'  match (amm_present,amm_frozen){(true,true)=>{'+REQ660+'}'); s(661,'  (_,false)=>if '+EMPTY+'{'+TCF+'}(false,true)=>{}}')
        elif part=='A6': s(659,'  match (amm_present,amm_frozen){(_,false)=>if '+EMPTY+'{'+TCF+'}'); s(660,'  (true,true)=>{'+REQ660+'}(false,true)=>{}}'); s(661,'')
        elif part=='A6b': s(659,'  match (amm_frozen,amm_present){(false,_)=>if '+EMPTY+'{'+TCF+'}'); s(660,'  (true,true)=>{'+REQ660+'}(true,false)=>{}}'); s(661,'')
        elif part=='A6c': s(659,'  match amm_frozen{false=>if '+EMPTY+'{'+TCF+'}'); s(660,'  true=>{'+REQ660+'}}'); s(661,'')
        elif part=='A6d': s(659,'  match (amm_present,amm_frozen){(_,false)=>if '+EMPTY+'{'+TCF+'}'); s(660,'  _=>{'+REQ660+'}}'); s(661,'')
        elif part=='A6e': s(659,'  if !amm_frozen{if '+EMPTY+'{'+TCF+'}}'); s(660,'  else{'+REQ660+'}'); s(661,'')
        elif part=='A6f': s(659,'  match (amm_present,amm_frozen){(_,false)=>if '+EMPTY+'{'+TCF+'}'); s(660,'  (true,true)|(false,true)=>{'+REQ660+'}}'); s(661,'')
        elif part=='A7': s(659,'  match (amm_present,amm_frozen){(false,_)=>{}'); s(660,'  (true,true)=>{'+REQ660+'}'); s(661,'  (true,false)=>{'+TCF+'}}')
        elif part=='N1': s(663,'  match native as i32{1=>{'+NH); s(664,NT+'}_=>{'+TH); s(720,'   Ok(amount)}}')
        elif part=='N2': s(663,'  match native as i32{0=>{'+TH); s(664,''); s(720,'   Ok(amount)}'); s(721,'  _=>{'+NH+NT.strip()+'}}')
        elif part in ('T1','T2','T3','T4','T5'):
            t=L[718]; P='   if frozen{'; assert t.startswith(P); k=t.index('}else if amount>0{'); REQ719=t[len(P):k]; TC=t[k+len('}else if amount>0{'):-1]
            if part=='T1': s(719,'   match (frozen,amount>0){(true,_)=>{'+REQ719+'}(false,true)=>{'+TC+'}(false,false)=>{}}')
            if part=='T2': s(719,'   match frozen as i32{1=>{'+REQ719+'}_=>if amount>0{'+TC+'}}')
            if part=='T3': s(719,'   match (frozen,amount>0){(false,true)=>{'+TC+'}(true,_)=>{'+REQ719+'}(false,false)=>{}}')
            if part=='T4': s(719,'   match (amount>0,frozen){(true,false)=>{'+TC+'}(_,true)=>{'+REQ719+'}(false,false)=>{}}')
            if part=='T5': s(719,'   match (frozen,amount){(false,0)=>{}(true,_)=>{'+REQ719+'}(false,_)=>{'+TC+'}}')
        elif part in ('P1','P2','P7','P8','P9'):
            TRA='token_raw_amount(a.coin_creator_vault_ata.as_ref())'; ER='PumpError::CtoSharedVaultFrozen'
            assert L[659]=='  if amm_frozen{require!('+TRA+'?==0,'+ER+');}'
            if part=='P1': s(660,'  if amm_frozen{match '+TRA+'{Ok(v)=>require!(v==0,'+ER+'),Err(e)=>return Err(e)}}')
            if part=='P2': s(660,'  if amm_frozen{match '+TRA+'{Err(e)=>return Err(e),Ok(v)=>require!(v==0,'+ER+')}}')
            if part=='P7': s(660,'  if amm_frozen{'+TRA+'.and_then(|v|{require!(v==0,'+ER+');Ok(())})?;}')
            if part=='P8': s(660,'  if amm_frozen{require!('+TRA+'.map(|v|v==0)?,'+ER+');}')
            if part=='P9': s(660,'  if amm_frozen{let amount='+TRA+'?;match amount as i32{0=>{},_=>require!(amount==0,'+ER+')}}')
        elif part in ('a1','t1'):
            FA='let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;'
            AF='let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;'
            assert L[663].count(FA)==1; s(664,L[663].replace(FA,AF))
            if part=='t1':
                t=L[718]
                for x,y in (('.to_account_info()})).and_then(|()|crate::collect_v2::transfer_vault_tokens(','.to_account_info()}))?;crate::collect_v2::transfer_vault_tokens('),('amount,&vsigner))?;return Ok(amount);}','amount,&vsigner)?;return Ok(amount);}')):
                    assert t.count(x)==1,x; t=t.replace(x,y)
                s(719,t)
        elif part=='V1':
            t=L[663]; assert t.count('(if amount>0{')==1 and t.count('}else{Ok(())})')==1
            s(664,t.replace('(if amount>0{','(match (amount>0) as i32{1=>{').replace('}else{Ok(())})','}_=>Ok(())})'))
        else: raise SystemExit('unknown '+part)
def make(base,var):
    s0=app(SRC,BASES[base]); L=s0.split('\n'); p=parts(L)
    lits=[x for x in var.split('+') if x.startswith('ev')]; var2='+'.join(x for x in var.split('+') if not x.startswith('ev')) or '-'
    old='\n'.join(L[LO-1:HI]); (V(var2,L,p) if var2!='-' else None); new='\n'.join(L[LO-1:HI])
    ed=list(BASES[base])+([(old,new)] if var2!='-' else [])
    for lt in lits:
        import sys as _s; _s.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a07-cto-sweeptuple/tools'); import lit
        t0=app(SRC,ed); order=[int(c,16) for c in {'ev6':'6012345789abc','ev7':'7012345689abc'}[lt]]
        a_,b_,fl=lit.fields(t0,'ev'); oldl=t0[a_:b_]; newl=','.join(fl[k] for k in order)
        assert t0.count(oldl)==1; ed.append((oldl,newl))
    t=app(SRC,ed); assert t.count('\n')==SRC.count('\n')
    nm=f"{base}_{var.replace('+','')}" if var!='-' else base+'_0'
    open(f'{E}/{nm}.py','w').write('EDITS='+repr(ed)+'\n'); return nm
if __name__=='__main__':
    bases=sys.argv[1].split(','); vs=sys.argv[2].split(',')
    print(' '.join(make(b,v) for b in bases for v in vs))
