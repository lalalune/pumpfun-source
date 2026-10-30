# w13a30-cto-stitch8 gene catalog, keyed on main 6ac6f9b67 (and w13a21 clonefeat, which only touches the sharing CPI line).
# Every gene keeps the newline count (apply() asserts it), so every line!() site is unchanged.
G = {}

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

# ---- skip tree tuple orders (w13a08 sweepphi / stitch cus) ----
_TQ = "let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};"
_U = {'u': ('sharing_update', 'Some(None)', 'Some(args.0)', 'None'), 'c': ('collect_old', 'false', 'false', '!st.holder_reward&&st.creator!=Pubkey::default()'), 's': ('skip', 'false', 'true', 'true')}
def _tq(order):
    n = ','.join(_U[k][0] for k in order)
    h = ','.join(_U[k][1] for k in order)
    nh = ','.join(_U[k][2] for k in order)
    ns = ','.join(_U[k][3] for k in order)
    return f"let ({n})=if shared{{if holder{{({h})}}else{{target=st.creator;({nh})}}}}else{{({ns})}};"
for o in ('cus', 'csu', 'scu', 'suc', 'usc'):
    G['t_' + o] = [(_TQ, _tq(o))]
# outer tuple orders (holder,cashback,target,sharing_update,collect_old,skip)
_OT = "(holder,cashback,target,sharing_update,collect_old,skip)"
G['o_skip_first'] = [("let " + _OT + "={", "let (skip,holder,cashback,target,sharing_update,collect_old)={"), (_OT + "};", "(skip,holder,cashback,target,sharing_update,collect_old)};")]
G['o_su_first'] = [("let " + _OT + "={", "let (sharing_update,holder,cashback,target,collect_old,skip)={"), (_OT + "};", "(sharing_update,holder,cashback,target,collect_old,skip)};")]
G['o_target_first'] = [("let " + _OT + "={", "let (target,holder,cashback,sharing_update,collect_old,skip)={"), (_OT + "};", "(target,holder,cashback,sharing_update,collect_old,skip)};")]
G['o_cb_hold'] = [("let " + _OT + "={", "let (cashback,holder,target,sharing_update,collect_old,skip)={"), (_OT + "};", "(cashback,holder,target,sharing_update,collect_old,skip)};")]
G['o_co_sk'] = [("let " + _OT + "={", "let (holder,cashback,target,sharing_update,skip,collect_old)={"), (_OT + "};", "(holder,cashback,target,sharing_update,skip,collect_old)};")]

# ---- Ok-tuple through `?` (w13a16) ----
_OK = "let (target,sharing_update)=Ok::<_,anchor_lang::error::Error>((target,sharing_update))?;"
G['ok_cb'] = [(_OK, "let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;")]
G['ok_hold'] = [(_OK, "let (target,sharing_update,holder)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,holder))?;")]
G['ok_swap'] = [(_OK, "let (sharing_update,target)=Ok::<_,anchor_lang::error::Error>((sharing_update,target))?;")]
G['ok_co'] = [(_OK, "let (target,sharing_update,collect_old)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,collect_old))?;")]
G['ok_skip'] = [(_OK, "let (target,sharing_update,skip)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,skip))?;")]

# ---- validate fee forms ----
_F0 = "match fee{Some(f)=>{if st.quote_locked"
_F1 = "CreatorFeeBpsOutOfRange));}}None=>{}}"
G['f_iflet'] = [(_F0, "if let Some(f)=fee{if st.quote_locked"), (_F1, "CreatorFeeBpsOutOfRange));}}")]
G['f_letelse'] = [(_F0, "let Some(f)=fee else{return Ok(target)};{if st.quote_locked"), (_F1, "CreatorFeeBpsOutOfRange));}}")]
G['f_none_first'] = [(_F0, "match fee{None=>{}Some(f)=>{if st.quote_locked"), (_F1, "CreatorFeeBpsOutOfRange));}}}")]

# ---- event sources ----
G['e_hr_curve'] = [("is_holder_reward:holder,", "is_holder_reward:a.bonding_curve.is_holder_reward,")]
G['e_cb_local'] = [("is_cashback_coin:a.bonding_curve.is_cashback_coin,", "is_cashback_coin:cashback,")]
G['e_nf_local'] = [("new_creator_fee_bps:a.bonding_curve.creator_fee_bps,", "new_creator_fee_bps:fee.unwrap_or(old_fee),")]
G['e_mint_key'] = [("authority:a.admin_set_creator_authority.key(),mint,bonding_curve", "authority:a.admin_set_creator_authority.key(),mint:a.mint.key(),bonding_curve")]
G['e_reset'] = [(" let signer_seeds:&[&[&[u8]]]=", " let reset=sharing_update.is_some();let signer_seeds:&[&[&[u8]]]="), ("sharing_config_reset:sharing_update.is_some(),", "sharing_config_reset:reset,")]
G['e_reset_late'] = [(" let pool_updated=a.pool.owner==", " let reset=sharing_update.is_some();let pool_updated=a.pool.owner=="), ("sharing_config_reset:sharing_update.is_some(),", "sharing_config_reset:reset,")]
G['e_ts_first'] = [(" let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,", " let timestamp=Clock::get()?.unix_timestamp;let e=AdminCtoEvent{timestamp,")]
G['e_auth_ctx'] = [("authority:a.admin_set_creator_authority.key(),mint", "authority:*a.admin_set_creator_authority.key,mint")]
G['e_bc_ref'] = [("bonding_curve:a.bonding_curve.key(),", "bonding_curve:*a.bonding_curve.to_account_info().key,")]
G['e_emit_ref'] = [("emit!(e);emit_cpi!(e);Ok(())", "emit!(e.clone());emit_cpi!(e);Ok(())")]

# ---- pool CPI ----
G['p_hr_local'] = [("signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;", "signer_seeds),target,holder,fee)?;")]
G['p_cr_curve'] = [("signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;", "signer_seeds),a.bonding_curve.creator,a.bonding_curve.is_holder_reward,fee)?;")]
G['p_empty_first'] = [("let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", "let pool_updated=!a.pool.data_is_empty()&&a.pool.owner==&AMM;")]
G['p_owner_deref'] = [("let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", "let pool_updated=*a.pool.owner==AMM && !a.pool.data_is_empty();")]
G['p_prog_let'] = [("  crate::pump_amm::cpi::admin_cto_pool(CpiContext::new_with_signer(a.pump_amm.to_account_info(),", "  let program=a.pump_amm.to_account_info();crate::pump_amm::cpi::admin_cto_pool(CpiContext::new_with_signer(program,")]
G['p_a_reborrow'] = [(" let a=&ctx.accounts;\n let pool_updated", " let a=&*ctx.accounts;\n let pool_updated")]

# ---- sharing CPI / signer seeds ----
G['s_su_iflet'] = [(" match sharing_update{Some(val)=>{", " if let Some(val)=sharing_update{"), (" }None=>{}}\n let (old_creator,old_fee)={", " }\n let (old_creator,old_fee)={")]
G['s_su_none_first'] = [(" match sharing_update{Some(val)=>{", " match sharing_update{None=>{}Some(val)=>{"), (" }None=>{}}\n let (old_creator,old_fee)={", " }}\n let (old_creator,old_fee)={")]
G['s_pbump'] = [(" let signer_seeds:&[&[&[u8]]]=&[&[b\"pool-authority\",mint.as_ref(),&[ctx.bumps.pool_authority]]];", " let pbump=[ctx.bumps.pool_authority];let signer_seeds:&[&[&[u8]]]=&[&[b\"pool-authority\",mint.as_ref(),&pbump]];")]
G['s_seeds_arr'] = [(" let signer_seeds:&[&[&[u8]]]=&[&[b\"pool-authority\",mint.as_ref(),&[ctx.bumps.pool_authority]]];", " let signer_seeds:&[&[&[u8]];1]=&[&[b\"pool-authority\",mint.as_ref(),&[ctx.bumps.pool_authority]]];")]

# ---- curve block ----
G['c_fee_unwrap'] = [("  if let Some(f)=fee{curve.creator_fee_bps=f;}\n", "  curve.creator_fee_bps=fee.unwrap_or(old_fee);\n")]
G['c_ce_first'] = [("let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;\n", "let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;curve.can_edit_creator_fee=false;\n"), ("  curve.can_edit_creator_fee=false;\n", "\n")]
G['c_ce_cr'] = [("  curve.creator=target;\n", "  curve.creator=target;curve.can_edit_creator_fee=false;\n"), ("  curve.can_edit_creator_fee=false;\n", "\n")]
G['c_of_first'] = [("let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;\n", "let old_fee=curve.creator_fee_bps;let old_creator=curve.creator;\n")]
G['c_hr_cb'] = [("  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;\n", "  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n")]

# ---- entry ----
_SU = "let shared=if a.bonding_curve.creator==a.sharing_config.key(){a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()}else{false};"
G['u_sand'] = [(_SU, "let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();")]
G['u_sof'] = [(_SU, "let shared=if a.sharing_config.owner==&FEES{a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty()}else{false};")]
G['u_sof2'] = [(_SU, "let shared=if a.bonding_curve.creator==a.sharing_config.key(){!a.sharing_config.data_is_empty()&&a.sharing_config.owner==&FEES}else{false};")]
G['u_sof3'] = [(_SU, "let shared=a.sharing_config.owner==&FEES&&a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty();")]
G['u_nested'] = [(_SU, "let shared=if a.bonding_curve.creator==a.sharing_config.key(){if a.sharing_config.owner==&FEES{!a.sharing_config.data_is_empty()}else{false}}else{false};")]
G['n_cb_rev'] = [("let cashback=st.cashback&&!holder;", "let cashback=!holder&&st.cashback;")]
G['n_cb_if'] = [("let cashback=st.cashback&&!holder;", "let cashback=if holder{false}else{st.cashback};")]
G['n_sk_inline'] = [("let sk=a.sharing_config.key();", ""), ("&holder_key,&sk)?;", "&holder_key,&a.sharing_config.key())?;")]
G['n_hk_direct'] = [("let holder_key;let hk=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);holder_key=hk.0;", "let hk=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);let holder_key=hk.0;")]

# ---- sweep ----
G['w_tf_prog'] = [("  else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(a.pump_amm.to_account_info(),", "  else if !a.coin_creator_vault_ata.data_is_empty(){let program=a.pump_amm.to_account_info();crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(program,")]
G['w_bump_scalar'] = [("let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&bump];", "let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&[bump]];")]
G['w_ob'] = [("let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();", "let old=a.current_creator.key();let bump=[ctx.bumps.creator_vault];")]
G['w_rref'] = [("let min=Rent::get()?.minimum_balance(0);", "let rent=&Rent::get()?;let min=rent.minimum_balance(0);")]
G['w_rl'] = [("let min=Rent::get()?.minimum_balance(0);", "let rent=Rent::get()?;let min=rent.minimum_balance(0);")]
G['w_ammif'] = [("let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(a.coin_creator_vault_ata.as_ref())?;", "let amm_frozen=if a.coin_creator_vault_ata.data_is_empty(){false}else{token_frozen(a.coin_creator_vault_ata.as_ref())?};")]
G['w_destrev'] = [("if a.holder_creator_vault.key()!=dest{", "if dest!=a.holder_creator_vault.key(){")]
G['w_dborrow'] = [("if a.holder_creator_vault.key()!=dest{", "if *a.holder_creator_vault.key!=dest{")]
G['w_vsig_ref'] = [("let vsigner:[&[&[u8]];1];let bump=", "let bump="), ("vsigner=[vaultseeds];", "let vsigner:&[&[&[u8]];1]=&[vaultseeds];"), ("amount,&vsigner).map(|()|amount)", "amount,vsigner).map(|()|amount)"), ("amount,&vsigner)?;}", "amount,vsigner)?;}")]
G['w_vsig_first_bo'] = [("let vsigner:[&[&[u8]];1];let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();", "let old=a.current_creator.key();let vsigner:[&[&[u8]];1];let bump=[ctx.bumps.creator_vault];")]
G['w_vsig_mid'] = [("let vsigner:[&[&[u8]];1];let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();", "let bump=[ctx.bumps.creator_vault];let vsigner:[&[&[u8]];1];let old=a.current_creator.key();")]
G['w_vsig_late'] = [("let vsigner:[&[&[u8]];1];let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();", "let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vsigner:[&[&[u8]];1];")]
G['w_gate_res'] = [("swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);", "swept=if !skip{sweep(&ctx,&holder_key)}else{Ok(0)}?;")]
G['w_gate_if'] = [("swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);", "swept=if !skip{sweep(&ctx,&holder_key)?}else{0};")]
G['w_native_late'] = [("->Result<u64>{let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;", "->Result<u64>{let a=&ctx.accounts;"), ("vsigner=[vaultseeds];", "vsigner=[vaultseeds];let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;")]

# ---- wallet ----
_EV = """         ({let event_inner:&[&[u8]]=&[b"__event_authority",&[authority_bump]];
         event_signers=[event_inner];
         anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&event_signers)}).map_err(anchor_lang::error::Error::from)?;"""
G['x_einfo_inline'] = [("let event_infos=[authority_info];({let", "({let"), ("invoke_signed(&ix,&event_infos,&event_signers)", "invoke_signed(&ix,&[authority_info],&event_signers)")]
G['x_einfo_in'] = [("let event_infos=[authority_info];({let event_inner:&[&[u8]]=&[b\"__event_authority\",&[authority_bump]];", "({let event_inner:&[&[u8]]=&[b\"__event_authority\",&[authority_bump]];let event_infos=[authority_info];")]
G['x_cp_inline'] = [("  let coin_present=!a.coin_creator_vault_ata.data_is_empty();\n", "\n"), ("  let do_coin=coin_present&&", "  let coin_present=!a.coin_creator_vault_ata.data_is_empty();let do_coin=coin_present&&")]
G['x_ata_rev'] = [("if !collection_native||coin_present{", "if coin_present||!collection_native{")]
G['x_dc_if'] = [("  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;", "  let do_coin=if coin_present{!token_frozen(a.coin_creator_vault_ata.as_ref())?}else{false};")]
G['x_dcol_if'] = [("  let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);", "  let do_collect=if collection_native{true}else{!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?};")]
G['x_co_if'] = [(" if collect_old{wallet(&ctx)?;}", " if collect_old{wallet(&ctx)?}")]
G['x_co_then'] = [(" if collect_old{wallet(&ctx)?;}", " collect_old.then(||wallet(&ctx)).transpose()?;")]

# ---- keyed on composite e1 (d81d0f588 + ok_cb + w_bump_scalar) ----
_OK2 = "let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;"
G['k_okcb_hold'] = [(_OK2, "let (target,sharing_update,cashback,holder)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,holder))?;")]
G['k_okcb_co'] = [(_OK2, "let (target,sharing_update,cashback,collect_old)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,collect_old))?;")]
G['k_okcb_skip'] = [(_OK2, "let (target,sharing_update,cashback,skip)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,skip))?;")]
G['k_okcb_cfirst'] = [(_OK2, "let (cashback,target,sharing_update)=Ok::<_,anchor_lang::error::Error>((cashback,target,sharing_update))?;")]
G['k_okcb_mid'] = [(_OK2, "let (target,cashback,sharing_update)=Ok::<_,anchor_lang::error::Error>((target,cashback,sharing_update))?;")]
G['k_bs_ob'] = [("let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();", "let old=a.current_creator.key();let bump=ctx.bumps.creator_vault;")]
G['k_bs_vlate'] = [("let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();", "let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vsigner:[&[&[u8]];1];")]
G['k_bs_inline'] = [("let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&[bump]];", "let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&[ctx.bumps.creator_vault]];")]
# ---- sharing-CPI clone field orders (llc fieldscan on a6412c2: O3071 pump_fees owner-early, K3245 mint key-late) ----
_FL = lambda e, order: '{let x=&*' + e + ';AccountInfo{' + ','.join({'k': 'key:x.key', 'o': 'owner:x.owner', 'l': 'lamports:x.lamports.clone()', 'd': 'data:x.data.clone()', 'r': 'rent_epoch:x.rent_epoch', 's': 'is_signer:x.is_signer', 'w': 'is_writable:x.is_writable', 'e': 'executable:x.executable'}[c] for c in order) + '}}'
G['z_o_pf'] = [("CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{", "CpiContext::new_with_signer(" + _FL('a.pump_fees', 'koldrswe') + ",crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{")]
G['z_k_mint'] = [("global:a.global.to_account_info(),mint:a.mint.to_account_info(),sharing_config", "global:a.global.to_account_info(),mint:" + _FL('a.mint', 'ldkorswe') + ",sharing_config")]
