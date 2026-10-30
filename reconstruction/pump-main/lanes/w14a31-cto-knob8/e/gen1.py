import json,os
OUT=os.path.dirname(os.path.abspath(__file__))
V={
# tail / pool gate / msg
'tp_dlen':[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;","let pool_updated=a.pool.data_len()!=0 && a.pool.owner==&AMM;")],
'tp_ownderef':[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;","let pool_updated=!a.pool.data_is_empty() && *a.pool.owner==AMM;")],
'tp_owneq':[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;","let pool_updated=!a.pool.data_is_empty() && a.pool.owner.eq(&AMM);")],
'tp_ifelse':[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;","let pool_updated=if a.pool.data_is_empty(){false}else{a.pool.owner==&AMM};")],
'tp_solog':[('}else{msg!("No canonical pump pool for this mint; curve only");}','}else{anchor_lang::solana_program::log::sol_log("No canonical pump pool for this mint; curve only");}')],
'tp_neg':[(" if pool_updated{\n"," if !pool_updated{msg!(\"No canonical pump pool for this mint; curve only\");}else{\n"),('}else{msg!("No canonical pump pool for this mint; curve only");}','}')],
'tp_pargs_hold':[("let pargs=(target,a.bonding_curve.is_holder_reward,fee);","let pargs=(a.bonding_curve.creator,a.bonding_curve.is_holder_reward,fee);")],
'tp_pargs_split':[("let pargs=(target,a.bonding_curve.is_holder_reward,fee);","let pargs=(target,a.bonding_curve.is_holder_reward,fee);let (pt,ph,pf)=pargs;"),("signer_seeds),pargs.0,pargs.1,pargs.2)?;","signer_seeds),pt,ph,pf)?;")],
# event
'ev_reset_matches':[("sharing_config_reset:sharing_update.is_some(),","sharing_config_reset:matches!(sharing_update,Some(_)),")],
'ev_reset_ne':[("sharing_config_reset:sharing_update.is_some(),","sharing_config_reset:!sharing_update.is_none(),")],
'ev_bc_deref':[("bonding_curve:a.bonding_curve.key(),old_creator","bonding_curve:*a.bonding_curve.to_account_info().key,old_creator")],
'ev_bc_asref':[("bonding_curve:a.bonding_curve.key(),old_creator","bonding_curve:*AsRef::<AccountInfo>::as_ref(&a.bonding_curve).key,old_creator")],
'ev_auth_deref':[("authority:a.admin_set_creator_authority.key(),mint,","authority:*a.admin_set_creator_authority.key,mint,")],
'ev_ts_unwrap':[("let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,","let e=AdminCtoEvent{timestamp:Clock::get().map(|c|c.unix_timestamp)?,")],
'ev_ts_sysvar':[("let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,","let e=AdminCtoEvent{timestamp:<Clock as anchor_lang::solana_program::sysvar::Sysvar>::get()?.unix_timestamp,")],
'ev_emit_ref':[("pool_updated};emit!(e);emit_cpi!(e);Ok(())","pool_updated};emit!(e);emit_cpi!(e);Ok::<(),anchor_lang::error::Error>(())")],
# wallet
'wl_exec_owner_deref':[("else if a.current_creator.owner!=&anchor_lang::system_program::ID{","else if *a.current_creator.owner!=anchor_lang::system_program::ID{")],
'wl_writable_req':[("if !a.current_creator.is_writable{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}","require!(a.current_creator.is_writable,PumpError::CtoCreatorAccountNotWritable);")],
'wl_native_deref':[("  let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;","  let collection_native=*a.quote_mint.to_account_info().key==anchor_spl::token::spl_token::native_mint::ID;")],
'wl_native_check':[("  let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;","  let collection_native=anchor_spl::token::spl_token::native_mint::check_id(&a.quote_mint.key());")],
'wl_coin_dlen':[("  let coin_present=!a.coin_creator_vault_ata.data_is_empty();","  let coin_present=a.coin_creator_vault_ata.data_len()!=0;")],
'wl_vq_dlen':[("(!a.creator_vault_quote_token_account.data_is_empty()&&","(a.creator_vault_quote_token_account.data_len()!=0&&")],
'wl_ev_creator_deref':[("creator:a.current_creator.key(),creator_fee:collected","creator:*a.current_creator.key,creator_fee:collected")],
'wl_ev_ts_map':[("let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,","let e=CollectCreatorFeeEvent{timestamp:Clock::get().map(|c|c.unix_timestamp)?,")],
'wl_disc_copied':[("disc.into_iter().map(|b|*b).chain(","disc.iter().copied().chain(")],
'wl_disc_cloned':[("disc.into_iter().map(|b|*b).chain(","disc.into_iter().cloned().chain(")],
'wl_meta_lit':[("vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]","vec![anchor_lang::solana_program::instruction::AccountMeta{pubkey:*authority_info.key,is_signer:true,is_writable:false}]")],
'wl_maperr_q':[("anchor_lang::solana_program::program::invoke_signed(&ix,&event_infos,&event_signers)}).map_err(anchor_lang::error::Error::from)?;","anchor_lang::solana_program::program::invoke_signed(&ix,&event_infos,&event_signers)}).map_err(|e|anchor_lang::error::Error::from(e))?;")],
'wl_bump_a':[("         let authority_bump=ctx.bumps.event_authority;","         let authority_bump=ctx.bumps.event_authority as u8;")],
'wl_cc_and':[("  if coin_present&do_coin{","  if do_coin{")],
'wl_cr_exec_first':[("if a.current_creator.executable{msg!(\"Creator is a program; fees left in the vaults\");}","if a.current_creator.executable==true{msg!(\"Creator is a program; fees left in the vaults\");}")],
# sweep
's_dest_pk':[("return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));","return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((*a.holder_creator_vault.key,dest)));")],
's_amount_ne':[("   if amount>0{crate::legacy_buy","   if amount!=0{crate::legacy_buy")],
's_tamount_ne':[("else if amount>0{anchor_spl::associated_token::create_idempotent","else if amount!=0{anchor_spl::associated_token::create_idempotent")],
's_req_if':[("   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}","   if frozen{if amount!=0{return Err(error!(PumpError::CtoSharedVaultFrozen));}}")],
's_req_if2':[("  if amm_frozen{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}","  if amm_frozen{if token_raw_amount(a.coin_creator_vault_ata.as_ref())?!=0{return Err(error!(PumpError::CtoSharedVaultFrozen));}}")],
's_rent_get':[("if native{let rent=Rent::get()?;let min=rent.minimum_balance(0);","if native{let min=Rent::get()?.minimum_balance(0);")],
's_lamports_sub':[("let amount=a.creator_vault.lamports().saturating_sub(min);","let amount=a.creator_vault.lamports().checked_sub(min).unwrap_or_default();")],
's_lamports_max':[("let amount=a.creator_vault.lamports().saturating_sub(min);","let l=a.creator_vault.lamports();let amount=if l>min{l-min}else{0};")],
's_native_deref':[("fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;","fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;let native=*a.quote_mint.to_account_info().key==anchor_spl::token::spl_token::native_mint::ID;")],
's_amm_dlen':[("  let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&","  let amm_frozen=a.coin_creator_vault_ata.data_len()!=0&&")],
's_elseif_dlen':[("  else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm","  else if a.coin_creator_vault_ata.data_len()!=0{crate::pump_amm")],
's_bump_arr':[("let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;","let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault as u8;")],
}
for n,e in V.items(): open(f'{OUT}/{n}.py','w').write('EDITS='+json.dumps(e)+'\n')
print(' '.join(V))
