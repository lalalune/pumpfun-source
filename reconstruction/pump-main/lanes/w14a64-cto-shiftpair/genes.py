# w14a64-cto-shiftpair genes: stitch11 library (genes_s11.py) + this lane's size-pair knobs
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_s11 as B
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
