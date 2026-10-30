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

# ---- comparison operand swaps and branch negations (main 308b545f1) ----
G['cmp_pool_rev'] = [("a.pool.owner==&AMM", "&AMM==a.pool.owner")]
G['cmp_fees_rev'] = [("a.sharing_config.owner==&FEES", "&FEES==a.sharing_config.owner")]
G['cmp_sh_rev'] = [("a.bonding_curve.creator==a.sharing_config.key()", "a.sharing_config.key()==a.bonding_curve.creator")]
G['cmp_hcv_rev'] = [("a.holder_creator_vault.key()!=dest", "dest!=a.holder_creator_vault.key()")]
G['cmp_nat_w'] = [("let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;", "let collection_native=anchor_spl::token::spl_token::native_mint::ID==a.quote_mint.key();")]
G['cmp_nat_s'] = [("let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;", "let native=anchor_spl::token::spl_token::native_mint::ID==a.quote_mint.key();")]
G['cmp_sys_rev'] = [("a.current_creator.owner!=&anchor_lang::system_program::ID", "&anchor_lang::system_program::ID!=a.current_creator.owner")]
G['cmp_amt1'] = [("if amount>0{crate::legacy_buy", "if 0<amount{crate::legacy_buy")]
G['cmp_amt2'] = [("}else if amount>0{anchor_spl", "}else if 0<amount{anchor_spl")]
G['cmp_cf_rev'] = [("a.bonding_curve.creator_fee==0", "0==a.bonding_curve.creator_fee")]
G['cmp_co_rev'] = [("st.creator!=Pubkey::default()", "Pubkey::default()!=st.creator")]
G['cmp_fmax_rev'] = [("f>st.max_fee", "st.max_fee<f")]
G['neg_pool'] = [("\n  if pool_updated{\n", "\n  if !pool_updated{msg!(\"No canonical pump pool for this mint; curve only\");}else{\n"), ("\n  }else{msg!(\"No canonical pump pool for this mint; curve only\");}\n", "\n  }\n")]
G['neg_shared'] = [("=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};", "=if !shared{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)}else if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)};")]
G['neg_sh_holder'] = [("=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{", "=if shared{if !holder{target=st.creator;(false,Some(args.0),true)}else{(false,Some(None),false)}}else{")]
import json as _j
G['neg_frozen'] = [tuple(_j.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'neg_frozen.json'))))]
_NC = 'msg!("No canonical pump pool for this mint; curve only");'
G['neg_pool'] = [("\n  if pool_updated{\n", "\n  if !pool_updated{" + _NC + "}else{\n"), ("\n  }else{" + _NC + "}\n", "\n  }\n")]
G['neg_pool'] = [("\n if pool_updated{\n", "\n if !pool_updated{" + _NC + "}else{\n"), ("\n }else{" + _NC + "}\n", "\n }\n")]

# ---- main 769f331fe: shared conjunct permutations, more comparison swaps ----
import itertools as _it
_SH6 = "let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();"
_C = {'k': "a.sharing_config.key()==a.bonding_curve.creator", 'K': "a.bonding_curve.creator==a.sharing_config.key()",
      'o': "a.sharing_config.owner==&FEES", 'O': "&FEES==a.sharing_config.owner", 'e': "!a.sharing_config.data_is_empty()"}
for _p in _it.permutations('koe'):
    for _kk in 'kK':
        for _oo in 'oO':
            _m = {'k': _kk, 'o': _oo, 'e': 'e'}
            _nm = 'shp_' + ''.join(_m[c] for c in _p)
            if _nm == 'shp_koe': continue
            G[_nm] = [(_SH6, "let shared=" + "&&".join(_C[_m[c]] for c in _p) + ";")]
G['cmp_v_hold'] = [("Result<Pubkey>{let holder=hopt==Some(true);", "Result<Pubkey>{let holder=Some(true)==hopt;")]
G['cmp_v_hr'] = [("if st.holder_reward&&!(hopt==Some(true)){", "if st.holder_reward&&!(Some(true)==hopt){")]
G['cmp_x_hold'] = [("let hopt=holder;let holder=hopt==Some(true);", "let hopt=holder;let holder=Some(true)==hopt;")]
G['cmp_v_tzero'] = [("  if t==Pubkey::default(){return Err(", "  if Pubkey::default()==t{return Err(")]
G['cmp_frz_amt'] = [("if frozen{require!(amount==0,", "if frozen{require!(0==amount,")]
G['cmp_amm_amt'] = [("token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,", "0==token_raw_amount(a.coin_creator_vault_ata.as_ref())?,")]
G['v_new_some'] = [("let target=if holder{if new.is_some(){return Err(", "let target=if holder{if !new.is_none(){return Err(")]
G['ev_reset_none'] = [("sharing_config_reset:sharing_update.is_some(),", "sharing_config_reset:!sharing_update.is_none(),")]
for _n in [k for k in list(G) if k.startswith('shp_')]:
    G['shq_' + ''.join({'k':'k','K':'kr','o':'o','O':'or','e':'e'}[c] for c in _n[4:])] = G[_n]
G['cmp_v_tsh1'] = [("if t==*sharing||t==*holder_key{", "if *sharing==t||t==*holder_key{")]
G['cmp_v_tsh2'] = [("if t==*sharing||t==*holder_key{", "if t==*sharing||*holder_key==t{")]
G['cmp_v_f0'] = [("if f==0||f>st.max_fee{", "if 0==f||f>st.max_fee{")]
G['x_dcol_in'] = [("(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?)", "(!token_frozen(a.creator_vault_quote_token_account.as_ref())?&&!a.creator_vault_quote_token_account.data_is_empty())")]
G['x_ata_dm'] = [("if !collection_native||coin_present{", "if !(collection_native&&!coin_present){")]
G['v_hr_some'] = [("if st.holder_reward&&!(hopt==Some(true)){", "if st.holder_reward&&!holder{")]

# ---- event-local lets rebased on 769f331fe (nf already before pool_updated) ----
_NF = "let nf=a.bonding_curve.creator_fee_bps;"
_PU6 = "let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;"
_EVA = "authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),"
for _pos in ('a', 'b'):   # a: before nf, b: between nf and pool_updated
    def _ins(x, _pos=_pos):
        return (_NF + _PU6, (x + _NF + _PU6) if _pos == 'a' else (_NF + x + _PU6))
    G['e6_cb_' + _pos] = [_ins("let cbc=a.bonding_curve.is_cashback_coin;"), ("is_cashback_coin:a.bonding_curve.is_cashback_coin,", "is_cashback_coin:cbc,")]
    G['e6_nc_' + _pos] = [_ins("let nc=a.bonding_curve.creator;"), ("new_creator:a.bonding_curve.creator,", "new_creator:nc,")]
    G['e6_hr_' + _pos] = [_ins("let hr=a.bonding_curve.is_holder_reward;"), ("is_holder_reward:a.bonding_curve.is_holder_reward,", "is_holder_reward:hr,")]
    G['e6_auth_' + _pos] = [_ins("let auth=a.admin_set_creator_authority.key();"), (_EVA, "authority:auth,mint,bonding_curve:a.bonding_curve.key(),")]
    G['e6_bc_' + _pos] = [_ins("let bck=a.bonding_curve.key();"), (_EVA, "authority:a.admin_set_creator_authority.key(),mint,bonding_curve:bck,")]
    G['e6_rs_' + _pos] = [_ins("let reset=sharing_update.is_some();"), ("sharing_config_reset:sharing_update.is_some(),", "sharing_config_reset:reset,")]
    G['e6_ts_' + _pos] = [_ins("let ts=Clock::get()?.unix_timestamp;"), ("let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,", "let e=AdminCtoEvent{timestamp:ts,")]
G['e6_nf_after'] = [(_NF + _PU6, _PU6 + _NF)]

# ---- main cef0574cf (wallet coin gate `if coin_present&&do_coin{`) ----
G['wc_rev'] = [("  if coin_present&&do_coin{", "  if do_coin&&coin_present{")]
G['wc_tf'] = [("  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;", "  let do_coin=!token_frozen(a.coin_creator_vault_ata.as_ref())?;"), ("  if coin_present&&do_coin{", "  if coin_present&&do_coin{")]

# ---- redundant-use (live-range) genes, main cef0574cf; each is equivalent by construction ----
G['ru_co_sh'] = [(" if collect_old{wallet(&ctx)?;}fn wallet", " if !shared&&collect_old{wallet(&ctx)?;}fn wallet")]
G['ru_co_sh2'] = [(" if collect_old{wallet(&ctx)?;}fn wallet", " if collect_old&&!shared{wallet(&ctx)?;}fn wallet")]
G['ru_skip_sh'] = [("swept=(!skip).then(||sweep(&ctx,&holder_key))", "swept=(!skip&&shared).then(||sweep(&ctx,&holder_key))")]
G['ru_skip_sh2'] = [("swept=(!skip).then(||sweep(&ctx,&holder_key))", "swept=(shared&&!skip).then(||sweep(&ctx,&holder_key))")]
G['ru_skip_hold'] = [("swept=(!skip).then(||sweep(&ctx,&holder_key))", "swept=(!skip&&holder).then(||sweep(&ctx,&holder_key))")]
G['ru_su_guard'] = [("match sharing_update{Some(val)=>{", "match sharing_update{Some(val) if shared=>{"), ("signer_seeds),val)?;\n\n }None=>{}}", "signer_seeds),val)?;\n\n }_=>{}}")]
G['ru_su_wild'] = [("signer_seeds),val)?;\n\n }None=>{}}", "signer_seeds),val)?;\n\n }_=>{}}")]
G['ru_pool_cp'] = [("let pargs=(target,a.bonding_curve.is_holder_reward,fee);", "let pargs=(target,a.bonding_curve.is_holder_reward,fee);let pool_updated=pool_updated&&!a.pool.data_is_empty();")]

# ---- quote_locked inline (main f8dc9016f, #3241): disjunct order and operand swaps ----
_QL8 = "let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};"
_QD = {'d': "q==Pubkey::default()", 'D': "Pubkey::default()==q", 'n': "q==anchor_spl::token::spl_token::native_mint::ID", 'N': "anchor_spl::token::spl_token::native_mint::ID==q", 'w': "a.global.whitelisted_quote_mints.contains(&q)"}
for _p in _it.permutations('dnw'):
    for _d in 'dD':
        for _n in 'nN':
            _m = {'d': _d, 'n': _n, 'w': 'w'}
            _nm = 'qlp_' + ''.join({'d':'d','D':'dr','n':'n','N':'nr','w':'w'}[_m[c]] for c in _p)
            if _nm == 'qlp_dnw': continue
            G[_nm] = [(_QL8, "let quote_locked={let q=a.bonding_curve.quote_mint;" + "||".join(_QD[_m[c]] for c in _p) + "};")]
G['ql_ref'] = [(_QL8, "let quote_locked={let q=&a.bonding_curve.quote_mint;*q==Pubkey::default()||*q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(q)};")]
