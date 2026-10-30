# w13a47-cto-stitch9 gene library keyed on main 52c0b087c. Every gene keeps the newline count.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genes30 as g30, knobs34 as k34
G = dict(g30.G)
for k, v in k34.K.items():
    G.setdefault(k, v)

def apply(names, src):
    s = src
    for n in names:
        for a, b in G[n]:
            c = s.count(a)
            if c != 1:
                raise ValueError(f'gene {n}: pattern count {c}: {a[:90]!r}')
            s = s.replace(a, b)
    if s.count('\n') != src.count('\n'):
        raise ValueError(f'genes {names}: newline count changed')
    return s

# w13a19 o_ab_late: execute's emit_cpi! hand-expanded, authority_bump read after ix
_EM = "emit!(e);emit_cpi!(e);Ok(())"
G['o_ab_late'] = [(_EM, "emit!(e);{let authority_info=ctx.accounts.event_authority.to_account_info();let disc=anchor_lang::event::EVENT_IX_TAG_LE;let inner_data=anchor_lang::Event::data(&e);let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);let authority_bump=ctx.bumps.event_authority;anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&[&[b\"__event_authority\",&[authority_bump]]]).map_err(anchor_lang::error::Error::from)?;}Ok(())")]
G['o_ab_early'] = [(_EM, "emit!(e);{let authority_info=ctx.accounts.event_authority.to_account_info();let authority_bump=ctx.bumps.event_authority;let disc=anchor_lang::event::EVENT_IX_TAG_LE;let inner_data=anchor_lang::Event::data(&e);let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&[&[b\"__event_authority\",&[authority_bump]]]).map_err(anchor_lang::error::Error::from)?;}Ok(())")]
# w13a19 s_rent_local
G['s_rent_local'] = [("if native{let min=Rent::get()?.minimum_balance(0);", "if native{let rent=Rent::get()?;let min=rent.minimum_balance(0);")]
# w13a19 ph: pool CPI holder from the local (+32 B)
G['ph'] = [("signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;", "signer_seeds),target,holder,fee)?;")]
# w13a24-3 k2: holder-rewards PDA before `shared`
_HK = "let holder_key;let hk=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);holder_key=hk.0;"
_SH = "let shared=if a.bonding_curve.creator==a.sharing_config.key(){a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()}else{false};"
G['k2'] = [(_SH + _HK, _HK + _SH)]
# w13a09 sweep transfer-CPI program let (current main's literal clone)
_TFX = "{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}"
G['w_tf_prog2'] = [("else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(" + _TFX + ",", "else if !a.coin_creator_vault_ata.data_is_empty(){let program=" + _TFX + ";crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(program,")]
G['w_tf_prog_tti'] = [("else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(" + _TFX + ",", "else if !a.coin_creator_vault_ata.data_is_empty(){let program=a.pump_amm.to_account_info();crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(program,")]
# pool_args_pre variants (w13a34 pool_args_pre binds (target,curve.is_holder_reward,fee) after pool_updated)
_PU = "let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();"
_PC1 = "},signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;"
G['pap_b'] = [(_PU, "let pargs=(target,a.bonding_curve.is_holder_reward,fee);" + _PU), (_PC1, "},signer_seeds),pargs.0,pargs.1,pargs.2)?;")]
G['pap_hr'] = [(_PU, _PU + "let phr=a.bonding_curve.is_holder_reward;"), (_PC1, "},signer_seeds),target,phr,fee)?;")]
G['pap_hr_b'] = [(_PU, "let phr=a.bonding_curve.is_holder_reward;" + _PU), (_PC1, "},signer_seeds),target,phr,fee)?;")]
G['pap_destr'] = [(_PU, _PU + "let (ptarget,phr,pfee)=(target,a.bonding_curve.is_holder_reward,fee);"), (_PC1, "},signer_seeds),ptarget,phr,pfee)?;")]
G['pap_th'] = [(_PU, _PU + "let pargs=(target,a.bonding_curve.is_holder_reward);"), (_PC1, "},signer_seeds),pargs.0,pargs.1,fee)?;")]

# ---- rebased on main 53abf28b1 (after #3168 pap+u_sand) ----
_PA = "let pargs=(target,a.bonding_curve.is_holder_reward,fee);"
G['pa_hold'] = [(_PA, "let pargs=(target,holder,fee);")]
G['pa_tcurve'] = [(_PA, "let pargs=(a.bonding_curve.creator,a.bonding_curve.is_holder_reward,fee);")]
G['pa_rot'] = [(_PA, "let pargs=(fee,target,a.bonding_curve.is_holder_reward);"), ("signer_seeds),pargs.0,pargs.1,pargs.2)?;", "signer_seeds),pargs.1,pargs.2,pargs.0)?;")]
G['pa_rot2'] = [(_PA, "let pargs=(a.bonding_curve.is_holder_reward,fee,target);"), ("signer_seeds),pargs.0,pargs.1,pargs.2)?;", "signer_seeds),pargs.2,pargs.0,pargs.1)?;")]
G['pa_ref'] = [(_PA, "let pargs=&(target,a.bonding_curve.is_holder_reward,fee);")]
G['pa_in'] = [(_PA + "\n  if pool_updated{", "\n  if pool_updated{" + _PA) ] if False else []
_SHN = "let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();"
G['sh_own_first'] = [(_SHN, "let shared=a.sharing_config.owner==&FEES&&a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty();")]
G['sh_empty_mid'] = [(_SHN, "let shared=a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty()&&a.sharing_config.owner==&FEES;")]
G['sh_key_rev'] = [(_SHN, "let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();")]
_HK2 = "let holder_key;let hk=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);holder_key=hk.0;"
G['k2n'] = [(_SHN + _HK2, _HK2 + _SHN)]
_QL = "let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);"
G['sh_after_ql'] = [(_SHN + _HK2 + _QL, _HK2 + _QL + _SHN)]
G['ql_first'] = [(_SHN + _HK2 + _QL, _QL + _SHN + _HK2)]
_OK = "let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;"
G['okp_uct'] = [(_OK, "let (sharing_update,cashback,target)=Ok::<_,anchor_lang::error::Error>((sharing_update,cashback,target))?;")]
G['okp_tcu'] = [(_OK, "let (target,cashback,sharing_update)=Ok::<_,anchor_lang::error::Error>((target,cashback,sharing_update))?;")]
G['okp_ctu'] = [(_OK, "let (cashback,target,sharing_update)=Ok::<_,anchor_lang::error::Error>((cashback,target,sharing_update))?;")]
G['okp_utc'] = [(_OK, "let (sharing_update,target,cashback)=Ok::<_,anchor_lang::error::Error>((sharing_update,target,cashback))?;")]
G['okp_cut'] = [(_OK, "let (cashback,sharing_update,target)=Ok::<_,anchor_lang::error::Error>((cashback,sharing_update,target))?;")]
G['okp_hold'] = [(_OK, "let (target,sharing_update,cashback,holder)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,holder))?;")]
G['okp_skip'] = [(_OK, "let (target,sharing_update,cashback,skip)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,skip))?;")]
G['okp_co'] = [(_OK, "let (target,sharing_update,cashback,collect_old)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,collect_old))?;")]
G['ev_hold'] = [("is_holder_reward:a.bonding_curve.is_holder_reward,", "is_holder_reward:holder,")]
G['ev_cbl'] = [("is_cashback_coin:a.bonding_curve.is_cashback_coin,", "is_cashback_coin:cashback,")]
G['ev_ncl'] = [("new_creator:a.bonding_curve.creator,", "new_creator:target,")]

# ---- && / || operand swaps (main 23322b07c) ----
G['n_cb_fwd'] = [("let cashback=!holder&&st.cashback;", "let cashback=st.cashback&&!holder;")]
G['v_hr_rev'] = [("if st.holder_reward&&!(hopt==Some(true)){", "if !(hopt==Some(true))&&st.holder_reward{")]
G['v_hr_ne'] = [("if st.holder_reward&&!(hopt==Some(true)){", "if st.holder_reward&&hopt!=Some(true){")]
G['v_he_a'] = [("if holder&&!st.holder_reward&&!st.holder_enabled{", "if !st.holder_reward&&holder&&!st.holder_enabled{")]
G['v_he_b'] = [("if holder&&!st.holder_reward&&!st.holder_enabled{", "if holder&&!st.holder_enabled&&!st.holder_reward{")]
G['v_he_c'] = [("if holder&&!st.holder_reward&&!st.holder_enabled{", "if !st.holder_enabled&&!st.holder_reward&&holder{")]
G['v_he_d'] = [("if holder&&!st.holder_reward&&!st.holder_enabled{", "if holder&&!(st.holder_reward||st.holder_enabled){")]
G['v_tsh_rev'] = [("if t==*sharing||t==*holder_key{", "if t==*holder_key||t==*sharing{")]
G['v_f_rev'] = [("if f==0||f>st.max_fee{", "if f>st.max_fee||f==0{")]
G['v_cbv_rev'] = [("let cashback=if holder{false}else{st.cashback};", "let cashback=!holder&&st.cashback;")]
G['v_cbv_fwd'] = [("let cashback=if holder{false}else{st.cashback};", "let cashback=st.cashback&&!holder;")]
G['co_rev'] = [("(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)", "(st.creator!=Pubkey::default()&&!st.holder_reward,None,true)")]
G['pu_rev'] = [("let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", "let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;")]
G['x_dcoin_rev'] = [("let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;", "let do_coin=!token_frozen(a.coin_creator_vault_ata.as_ref())?&&coin_present;")]
G['x_dcol_rev'] = [("let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);", "let do_collect=(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?)||collection_native;")]
G['w_af_rev'] = [("let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(a.coin_creator_vault_ata.as_ref())?;", "let amm_frozen=token_frozen(a.coin_creator_vault_ata.as_ref())?&&!a.coin_creator_vault_ata.data_is_empty();")]
G['v_hold_eq'] = [("fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);", "fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt.unwrap_or(false);")]
G['x_hold_eq'] = [("let hopt=holder;let holder=hopt==Some(true);", "let hopt=holder;let holder=hopt.unwrap_or(false);")]
G['x_hold_ml'] = [("let hopt=holder;let holder=hopt==Some(true);", "let hopt=holder;let holder=matches!(hopt,Some(true));")]
G['ev_nf_cbc'] = [("let nf=a.bonding_curve.creator_fee_bps;", "let nf=a.bonding_curve.creator_fee_bps;let cbc=a.bonding_curve.is_cashback_coin;"), ("is_cashback_coin:a.bonding_curve.is_cashback_coin,", "is_cashback_coin:cbc,")]
G['ev_nf_late'] = [("let nf=a.bonding_curve.creator_fee_bps;let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", "let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();let nf=a.bonding_curve.creator_fee_bps;")]
G['ev_nf_after_pargs'] = [("let nf=a.bonding_curve.creator_fee_bps;let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();let pargs=(target,a.bonding_curve.is_holder_reward,fee);", "let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();let pargs=(target,a.bonding_curve.is_holder_reward,fee);let nf=a.bonding_curve.creator_fee_bps;")]
G['rent_drop'] = [("if native{let rent=Rent::get()?;let min=rent.minimum_balance(0);", "if native{let min=Rent::get()?.minimum_balance(0);")]

# ---- fieldscan R3160 on 53abf28: sharing CPI authority clone, rent_epoch before the lamports Rc ----
_AU = "authority:a.admin_set_creator_authority.to_account_info(),global:{"
G['sc_auth_r'] = [(_AU, "authority:{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();AccountInfo{key:x.key,rent_epoch:x.rent_epoch,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},global:{")]
G['sc_auth_lit'] = [(_AU, "authority:{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},global:{")]
G['sc_auth_r2'] = [(_AU, "authority:{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();AccountInfo{rent_epoch:x.rent_epoch,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},global:{")]

# ---- execute preamble reorders (main 23322b07c) ----
_PRE = "let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
G['pre_sk_args'] = [(_PRE, "let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;let sk=a.sharing_config.key();let args=&(new,);let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
G['pre_args_late'] = [(_PRE, "let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let args=&(new,);")]
G['pre_cb_mid'] = [(_PRE, "let hopt=holder;let holder=hopt==Some(true);let args=&(new,);let cashback=!holder&&st.cashback;let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
G['pre_cb_sk'] = [(_PRE, "let hopt=holder;let holder=hopt==Some(true);let args=&(new,);let sk=a.sharing_config.key();let cashback=!holder&&st.cashback;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
G['pre_cb_late'] = [(_PRE, "let hopt=holder;let holder=hopt==Some(true);let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let cashback=!holder&&st.cashback;")]
G['pre_sk_first'] = [(_PRE, "let sk=a.sharing_config.key();let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;let args=&(new,);let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
G['pre_cb_hopt'] = [(_PRE, "let hopt=holder;let holder=hopt==Some(true);let cashback=!(hopt==Some(true))&&st.cashback;let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
G['pre_cb_match'] = [(_PRE, "let hopt=holder;let holder=hopt==Some(true);let cashback=match hopt{Some(true)=>false,_=>st.cashback};let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
G['pre_cb_not'] = [(_PRE, "let hopt=holder;let holder=hopt==Some(true);let cashback=!(holder||!st.cashback);let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
