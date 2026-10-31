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
