# w14a64-cto-shiftpair genes: stitch11 library (genes_s11.py) + this lane's size-pair knobs
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_s11b as B
G=B.G
def apply(s,names): return B.apply(s,names)
_ST=")={ let st=CtoState{"
_TG="else{target=st.creator;(false,Some(args.0),true)}"
G['s8take']=[(_ST,")={ let mut st=CtoState{"),(_TG,"else{target=core::mem::take(&mut st.creator);(false,Some(args.0),true)}")]
G['s10repl']=[(_ST,")={ let mut st=CtoState{"),(_TG,"else{target=core::mem::replace(&mut st.creator,Pubkey::default());(false,Some(args.0),true)}")]
# +8 candidates in the sweep native arm / wallet head (shift oracle: cu_iflet2 + pure +8 at cand 0x5930-0x5af8 = M +4 over main)
G['wl_writ_eq']=[("if !a.current_creator.is_writable{return","if a.current_creator.is_writable==false{return")]
_K3="CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),"
G['k3']=[(_K3,"CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:a.pump_amm.data.clone(),")]
_MIN="let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);"
G['r_getdot2']=[(_MIN,"let min=Rent::get()?.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);")]
G['r_letrent2']=[(_MIN,"let rent=Rent::get()?;let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);")]
G['r_inl']=[(_MIN,"let amount=a.creator_vault.lamports().saturating_sub({let rent=Rent::get()?;rent.minimum_balance(0)});")]
G['r_lamvar']=[(_MIN,"let min={let rent=Rent::get()?;rent.minimum_balance(0)};let lamports=a.creator_vault.lamports();let amount=lamports.saturating_sub(min);")]
G['r_ifsub']=[(_MIN,"let min={let rent=Rent::get()?;rent.minimum_balance(0)};let lamports=a.creator_vault.lamports();let amount=if lamports>min{lamports-min}else{0};")]
G['r_rentref']=[(_MIN,"let min={let rent=&Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);")]
_E=B._ENS; _T=B._TN; _NA=B._NA
G['n_atok']=[(_NA,"(if amount>0{"+_E+"?;"+_T+"}else{Ok(())}).and_then(|()|Ok(amount))")]
G['n_ge1']=[(_NA,"(if amount>=1{"+_E+"?;"+_T+"}else{Ok(())}).map(|()|amount)")]
G['n_eq0first']=[(_NA,"if amount==0{Ok(0)}else{"+_E+"?;"+_T+".map(|()|amount)}")]
G['n_then']=[(_NA,"(amount>0).then(||->Result<()>{"+_E+"?;"+_T+"}).unwrap_or(Ok(())).map(|()|amount)")]
G['n_letr']=[(_NA,"{let r=if amount>0{"+_E+"?;"+_T+"}else{Ok(())};r.map(|()|amount)}")]
G['n_ensmap']=[(_NA,"(if amount>0{"+_E+".map_err(|e|e)?;"+_T+"}else{Ok(())}).map(|()|amount)")]
G['n_tnmap']=[(_NA,"(if amount>0{"+_E+"?;"+_T+".map_err(|e|e)}else{Ok(())}).map(|()|amount)")]
G['n_okamt']=[(_NA,"(if amount>0{"+_E+"?;"+_T+".map(|()|amount)}else{Ok(amount)})")]
G['n_match0']=[(_NA,"(match amount{0=>Ok(()),_=>{"+_E+"?;"+_T+"}}).map(|()|amount)")]
G['n_ensok']=[(_NA,"(if amount>0{"+_E+"?;"+_T+"}else{Ok(())}).map(|()|amount)".replace(_E+"?;","let ()="+_E+"?;"))]
G['wl_owner_chk']=[("else if a.current_creator.owner!=&anchor_lang::system_program::ID{","else if !anchor_lang::solana_program::system_program::check_id(a.current_creator.owner){")]
G['wl_frozen_let']=[("if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!","let cf=token_frozen(a.current_creator_quote_token_account.as_ref())?;if cf{msg!")]
G['wl_exec_ne']=[("if a.current_creator.executable{msg!","if a.current_creator.executable!=false{msg!")]
# ---- polarity knobs (`!x` <-> `x==false`): wl_writ_eq is +8 B with no other codegen change; screen every `!` site ----
G['p_feecfg']=[("if !st.fee_configurable{return","if st.fee_configurable==false{return")]
G['p_colnat']=[("if !collection_native||coin_present{","if collection_native==false||coin_present{")]
G['p_dc_empty']=[("collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&","collection_native||(a.creator_vault_quote_token_account.data_is_empty()==false&&")]
G['p_dc_frozen']=[("&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);","&&token_frozen(a.creator_vault_quote_token_account.as_ref())?==false);")]
G['p_docoin']=[("let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;","let do_coin=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?==false;")]
G['p_coinpres']=[("let coin_present=!a.coin_creator_vault_ata.data_is_empty();","let coin_present=a.coin_creator_vault_ata.data_is_empty()==false;")]
G['p_ammfz']=[("let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&","let amm_frozen=a.coin_creator_vault_ata.data_is_empty()==false&&")]
G['p_elseif']=[("else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm","else if a.coin_creator_vault_ata.data_is_empty()==false{crate::pump_amm")]
G['p_skip']=[("swept=(!skip).then(","swept=(skip==false).then(")]
G['p_289']=[("if st.holder_reward&&!(hopt==Some(true)){","if st.holder_reward&&(hopt==Some(true))==false{")]
G['p_296a']=[("if holder&&!st.holder_reward&&!st.holder_enabled{","if holder&&st.holder_reward==false&&!st.holder_enabled{")]
G['p_296b']=[("if holder&&!st.holder_reward&&!st.holder_enabled{","if holder&&!st.holder_reward&&st.holder_enabled==false{")]
G['p_shared']=[("a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();","a.sharing_config.owner==&FEES&&a.sharing_config.data_is_empty()==false;")]
G['p_cb']=[("let cashback=!holder&&st.cashback;","let cashback=holder==false&&st.cashback;")]
G['p_co']=[("(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)","(st.holder_reward==false&&st.creator!=Pubkey::default(),None,true)")]
G['p_pool']=[("let pool_updated=!a.pool.data_is_empty() &&","let pool_updated=a.pool.data_is_empty()==false &&")]
# ---- CPI AccountInfo literal -8 moves (Rc swap / re-read removal) for pairing with +8 knobs ----
import re as _re
_LIT=_re.compile(r'\{let x:&AccountInfo=[^}]*\}\}')
def _litk(k,fn):
    def g(s):
        ms=list(_LIT.finditer(s)); m=ms[k-1]; t=m.group(0); t2=fn(t); assert t2!=t,(k,t[:80])
        return s[:m.start()]+t2+s[m.end():]
    return [g]
def _swapLD(t):
    fs=_re.search(r'AccountInfo\{(.*)\}\}',t).group(1).split(',')
    il=[i for i,f in enumerate(fs) if f.startswith('lamports:')][0]; id_=[i for i,f in enumerate(fs) if f.startswith('data:')][0]
    fs[il],fs[id_]=fs[id_],fs[il]
    return t[:t.index('AccountInfo{')+12]+','.join(fs)+'}}'
def _unread(field):
    def f(t):
        acct=_re.search(r'=\s*(a\.[\w]+)',t).group(1)
        return _re.sub(_re.escape(acct)+r'\.'+field+r'\b','x.'+field,t)
    return f
for _k in range(1,10): G[f'sw{_k}']=_litk(_k,_swapLD)
G['ur3d']=_litk(3,_unread('data')); G['ur3o']=_litk(3,_unread('owner')); G['ur5r']=_litk(5,_unread('rent_epoch'))
G['ur9d']=_litk(9,_unread('data')); G['ur9l']=_litk(9,_unread('lamports'))
G['ur9o']=_litk(9,_unread('owner'))
G['p_amp']=[("let amm_present=!a.coin_creator_vault_ata.data_is_empty();","let amm_present=a.coin_creator_vault_ata.data_is_empty()==false;")]
G['p_elseif2']=[("else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm","else if a.coin_creator_vault_ata.data_is_empty()==false{crate::pump_amm")]
# ---- wallet body / entry spellings (main 304b03a shift map: +8 entry/0x2000-0x24e0, -8 wallet body 0x5cb0-0x62c0) ----
_CN="  let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;\n"
_CP="  let coin_present=!a.coin_creator_vault_ata.data_is_empty();\n"
G['w_cpfirst']=[(_CN+_CP,_CP+_CN)]
G['w_ccswap']=[("if coin_present&do_coin{","if do_coin&coin_present{")]
G['w_cconly']=[("if coin_present&do_coin{","if do_coin{")]
G['w_cc_and2']=[("if coin_present&do_coin{","if coin_present&&do_coin{")]
G['w_collmatch']=[("if let Some((collected,quote_mint))=crate::collect_v2::collect(","if let Some((collected,quote_mint))=match crate::collect_v2::collect("),
  (",&a.quote_token_program,a.system_program.as_ref())?{",",&a.quote_token_program,a.system_program.as_ref()){Ok(v)=>v,Err(e)=>return Err(e)}{")]
G['w_dcif']=[("let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);",
  "let do_collect=if collection_native{true}else{!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?};")]
G['w_docoinif']=[("let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;","let do_coin=if coin_present{!token_frozen(a.coin_creator_vault_ata.as_ref())?}else{false};")]
G['w_evfee_first']=[("let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:a.current_creator.key(),creator_fee:collected,quote_mint};","let e=CollectCreatorFeeEvent{creator_fee:collected,quote_mint,timestamp:Clock::get()?.unix_timestamp,creator:a.current_creator.key()};")]
G['w_bump_a']=[("let authority_bump=ctx.bumps.event_authority;","let authority_bump=ctx.bumps.event_authority as u8;")]
_QL="let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};"
G['e_ql_nat1']=[(_QL,"let quote_locked={let q=a.bonding_curve.quote_mint;q==anchor_spl::token::spl_token::native_mint::ID||q==Pubkey::default()||a.global.whitelisted_quote_mints.contains(&q)};")]
G['e_ql_ref']=[(_QL,"let quote_locked={let q=&a.bonding_curve.quote_mint;*q==Pubkey::default()||*q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(q)};")]
G['e_ql_wl1']=[(_QL,"let quote_locked={let q=a.bonding_curve.quote_mint;a.global.whitelisted_quote_mints.contains(&q)||q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID};")]
G['e_sh_deref']=[("let shared=a.sharing_config.key()==a.bonding_curve.creator&&","let shared=*a.sharing_config.key==a.bonding_curve.creator&&")]
G['e_sh_rev']=[("let shared=a.sharing_config.key()==a.bonding_curve.creator&&","let shared=a.bonding_curve.creator==a.sharing_config.key()&&")]
# ---- sweep head spellings (+8 hot zone of ur5r at cand 0x2468-0x24e8 on 39eb377) ----
_AF="let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;"
G['sh_af_if']=[(_AF,"let amm_frozen=if amm_present{token_frozen(a.coin_creator_vault_ata.as_ref())?}else{false};")]
G['sh_af_eqf']=[(_AF,"let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?==true;")]
_RQ="if amm_frozen{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}"
G['sh_rq_ne']=[(_RQ,"if amm_frozen{if token_raw_amount(a.coin_creator_vault_ata.as_ref())?!=0{return Err(error!(PumpError::CtoSharedVaultFrozen));}}")]
G['sh_rq_let']=[(_RQ,"if amm_frozen{let amt=token_raw_amount(a.coin_creator_vault_ata.as_ref())?;require!(amt==0,PumpError::CtoSharedVaultFrozen);}")]
G['sh_elseif_amp']=[("else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm","else if amm_present{crate::pump_amm")]
G['sh_dest_ne']=[("if a.holder_creator_vault.key()!=dest{return","if dest!=a.holder_creator_vault.key(){return")]
G['sh_dest_deref']=[("if a.holder_creator_vault.key()!=dest{return","if *a.holder_creator_vault.key!=dest{return")]
G['wl_writ_not2']=[("if a.current_creator.is_writable==false{return","if !a.current_creator.is_writable{return")]
# ---- w14a80 stitch12: entry-spelling leads (w14a77 entrykeycopy, crl = +2 M at +72 B on 0d04cf4) ----
_SH='a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
_SHT='&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
G['crl']=[(_SH,'{let cr=a.bonding_curve.creator;a.sharing_config.key()==cr}'+_SHT)]
G['crl_kd']=[(_SH,'{let cr=a.bonding_curve.creator;*a.sharing_config.key==cr}'+_SHT)]
G['crl_kdL']=[(_SH,'{let cr=a.bonding_curve.creator;cr==*a.sharing_config.key}'+_SHT)]
G['crl_L']=[(_SH,'{let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}'+_SHT)]
G['crl_sk']=[(_SH,'{let cr=a.bonding_curve.creator;let sk=a.sharing_config.key();sk==cr}'+_SHT)]
G['crl_ref']=[(_SH,'{let cr=a.bonding_curve.creator;a.sharing_config.key()==*&cr}'+_SHT)]
G['crl_eq']=[(_SH,'{let cr=a.bonding_curve.creator;a.sharing_config.key().eq(&cr)}'+_SHT)]
G['hkmut']=[('let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;','let mut holder_key=Pubkey::default();let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;')]
# ---- w14a72 rescan304 C0 base (main 0d04cf4 minus wl ==false, sharing match, pool_authority rent re-read): M 2224 @27,376 ----
G['sm_iflet']=[("\n match sharing_update{Some(val)=>{\n","\n if let Some(val)=sharing_update{\n"),("\n }None=>{}}\n let (old_creator","\n }\n let (old_creator")]
G['C0']=G['wl_writ_not2']+G['sm_iflet']+G['ur5r']
G['wl_ts_clockvar']=[("let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,","let clock=Clock::get()?;let e=CollectCreatorFeeEvent{timestamp:clock.unix_timestamp,")]
G['g_s7_dborrow']=[('if a.holder_creator_vault.key()!=dest{', 'if *a.holder_creator_vault.key!=dest{')]
G['sh_prog_let']=[('crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{', 'let prog=a.pump_fees.to_account_info();crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(prog,crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{')]
G['cu_replace']=[('let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;', 'let old_creator=core::mem::replace(&mut curve.creator,target);let old_fee=curve.creator_fee_bps;'), ('  curve.creator=target;\n', '\n')]
G['g_w_clock_local']=[('     let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,', '     let ts=Clock::get()?.unix_timestamp;let e=CollectCreatorFeeEvent{timestamp:ts,')]
G['X']=G['C0']+G['crl_L']
# crl_L variants that reuse the creator copy (the copy is what matches orig 0x100-0x138)
G['crh']=[('let shared='+_SH,'let cr=a.bonding_curve.creator;let shared=cr==a.sharing_config.key()'+_SHT)]
G['crh_st']=G['crh']+[('let st=CtoState{creator:a.bonding_curve.creator,','let st=CtoState{creator:cr,')]
G['crh_su']=G['crh']+[('target=a.bonding_curve.creator;r}','target=cr;r}')]
G['crh_st_su']=G['crh_st']+[('target=a.bonding_curve.creator;r}','target=cr;r}')]
G['crl_L_st']=G['crl_L']+[('let st=CtoState{creator:a.bonding_curve.creator,','let st=CtoState{creator:a.bonding_curve.creator.clone(),')]
G['crh_ev']=G['crh']+[('old_creator,new_creator:a.bonding_curve.creator,','old_creator,new_creator:a.bonding_curve.creator,')]
