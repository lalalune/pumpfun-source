"""Semantically equivalent, line-count-preserving source permutations of admin_cto.rs.

Each gene is a list of (old, new) replacements; every old string must occur exactly once
in the file the gene is applied to.  No gene adds or removes a line, and no error!/require!
site moves to another line, so line!() immediates are unchanged.
"""
G = {}
# ---- wallet (556-569) ----
G['w-present-order'] = [(
 "let coin_present=!a.coin_creator_vault_ata.data_is_empty();let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();",
 "let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();let coin_present=!a.coin_creator_vault_ata.data_is_empty();")]
G['w-source-present-operands'] = [(
 "let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();",
 "let source_present=!a.creator_vault_quote_token_account.data_is_empty()&&!collection_native;")]
G['w-source-frozen-drop-native'] = [(
 "let source_frozen=!collection_native&&source_present&&token_frozen(",
 "let source_frozen=source_present&&token_frozen(")]
G['w-frozen-line-swap'] = [(
 "  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;\n  let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;",
 "  let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;\n  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;")]
G['w-ata-gate-or-rev'] = [("if !collection_native||coin_present{", "if coin_present||!collection_native{")]
G['w-collect-gate-or-rev'] = [("if collection_native||(source_present&&!source_frozen){", "if (source_present&&!source_frozen)||collection_native{")]
G['w-collect-gate-and-rev'] = [("if collection_native||(source_present&&!source_frozen){", "if collection_native||(!source_frozen&&source_present){")]
G['w-coin-gate-and-rev'] = [("if coin_present&&!coin_frozen{", "if !coin_frozen&&coin_present{")]
G['w-writable-require'] = [("if !a.current_creator.is_writable{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}",
 "require!(a.current_creator.is_writable,PumpError::CtoCreatorAccountNotWritable);")]
G['w-owner-ne-rev'] = [("else if a.current_creator.owner!=&anchor_lang::system_program::ID{", "else if &anchor_lang::system_program::ID!=a.current_creator.owner{")]
G['w-native-eq-rev'] = [("let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;",
 "let collection_native=anchor_spl::token::spl_token::native_mint::ID==a.quote_mint.key();")]
G['w-collect-old-gate-early-return'] = [("if collect_old{wallet(&ctx)?;}", "if !collect_old{}else{wallet(&ctx)?;}")]
# ---- sweep (647-726) ----
G['s-dest-ne-rev'] = [("if a.holder_creator_vault.key()!=dest{", "if dest!=a.holder_creator_vault.key(){")]
G['s-amm-frozen-no-empty'] = [("let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(", "let amm_frozen=token_frozen(")]
G['s-raw-zero-rev'] = [("require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,", "require!(0==token_raw_amount(a.coin_creator_vault_ata.as_ref())?,")]
G['s-native-amount-ne0'] = [("   if amount>0{crate::legacy_buy", "   if amount!=0{crate::legacy_buy")]
G['s-token-amount-ne0'] = [("else if amount>0{anchor_spl", "else if amount!=0{anchor_spl")]
G['s-token-frozen-first'] = [("let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;",
 "let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;")]
G['s-sat-sub-explicit'] = [("let amount=a.creator_vault.lamports().saturating_sub(min);",
 "let l=a.creator_vault.lamports();let amount=if l>min{l-min}else{0};")]
G['s-sat-sub-checked'] = [("let amount=a.creator_vault.lamports().saturating_sub(min);",
 "let amount=a.creator_vault.lamports().checked_sub(min).unwrap_or(0);")]
G['s-old-before-bump'] = [("let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();", "let old=a.current_creator.key();let bump=[ctx.bumps.creator_vault];")]
G['s-gate-and-rev'] = [("if shared && holder{swept=sweep(", "if holder && shared{swept=sweep(")]
G['s-native-eq-rev'] = [("let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;",
 "let native=anchor_spl::token::spl_token::native_mint::ID==a.quote_mint.key();")]
G['s-amm-else-polarity'] = [("  else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm", "  else if a.coin_creator_vault_ata.data_is_empty(){}else{crate::pump_amm")]
G['s-native-amount-polarity'] = [("   if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt", "   if amount==0{}else{crate::legacy_buy::native_payments::ensure_rent_exempt")]
# ---- curve store / tail (745-767) ----
G['t-store-hr-cb-swap'] = [("  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;", "  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;")]
G['t-store-creator-hr-swap'] = [("  curve.creator=target;\n  curve.is_holder_reward=holder;", "  curve.is_holder_reward=holder;\n  curve.creator=target;")]
G['t-store-fee-edit-swap'] = [("  if let Some(f)=fee{curve.creator_fee_bps=f;}\n  curve.can_edit_creator_fee=false;", "  curve.can_edit_creator_fee=false;\n  if let Some(f)=fee{curve.creator_fee_bps=f;}")]
G['t-store-fee-unwrap-or'] = [("  if let Some(f)=fee{curve.creator_fee_bps=f;}", "  curve.creator_fee_bps=fee.unwrap_or(old_fee);")]
G['t-old-fee-first'] = [("let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;", "let old_fee=curve.creator_fee_bps;let old_creator=curve.creator;")]
G['t-pool-and-rev'] = [("let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", "let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;")]
G['t-pool-eq-rev'] = [("let pool_updated=a.pool.owner==&AMM && ", "let pool_updated=&AMM==a.pool.owner && ")]
G['t-pool-polarity'] = [(" if pool_updated{\n", " if !pool_updated{msg!(\"No canonical pump pool for this mint; curve only\");}else{\n"),
                        (" }else{msg!(\"No canonical pump pool for this mint; curve only\");}", " }")]
G['t-ev-new-locals'] = [("new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,",
 "new_creator:target,is_holder_reward:holder,is_cashback_coin:cashback,")]
G['t-ev-newfee-local'] = [("new_creator_fee_bps:a.bonding_curve.creator_fee_bps,", "new_creator_fee_bps:fee.unwrap_or(old_fee),")]
G['t-ev-reset-match'] = [("sharing_config_reset:sharing_update.is_some(),", "sharing_config_reset:!sharing_update.is_none(),")]
G['t-sharing-if-let-clone'] = [(" if let Some(val)=sharing_update{\n", " if let Some(val)=sharing_update.clone(){\n")]
# ---- validate (283-338) ----
G['v-none-check-is-some'] = [("if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}", "if let Some(_)=new{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}")]
G['v-zero-key-eq-rev'] = [("if t==Pubkey::default(){", "if Pubkey::default()==t{")]
G['v-fee-zero-rev'] = [("if f==0||f>st.max_fee{", "if f>st.max_fee||f==0{")]
G['v-fee-cb-and-rev'] = [("if !holder&&st.cashback{return", "if st.cashback&&!holder{return")]
G['v-he-and-rev'] = [("if holder&&!st.holder_reward&&!st.holder_enabled{", "if holder&&!st.holder_enabled&&!st.holder_reward{")]
# ---- round 2 ----
G['s-amm-nested'] = [("  if amm_frozen{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}\n  else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm",
 "  if !a.coin_creator_vault_ata.data_is_empty(){if amm_frozen{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}\n  else {crate::pump_amm"),
 ("pump_creator_vault_ata:a.creator_vault_quote_token_account.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()}))?;}\n", "pump_creator_vault_ata:a.creator_vault_quote_token_account.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()}))?;}}\n")]
G['s-token-polarity'] = [("   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{", "   if !frozen{if amount>0{"),
 ("amount,&[vaultseeds])?;}\n   amount};", "amount,&[vaultseeds])?;}}else{require!(amount==0,PumpError::CtoSharedVaultFrozen);}\n   amount};")]
G['w-frozen-polarity'] = [("if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!(\"Creator quote token account is frozen; fees left in the vaults\");}else{",
 "if !token_frozen(a.current_creator_quote_token_account.as_ref())?{"),
 (" }}Ok(())}", " }else{msg!(\"Creator quote token account is frozen; fees left in the vaults\");}}Ok(())}")]
# ---- curve store order: all permutations of creator(C)/holder_reward(H)/cashback(B), lines 754-756 ----
_ST = {'C': "  curve.creator=target;", 'H': "  curve.is_holder_reward=holder;", 'B': "  curve.is_cashback_coin=cashback;"}
for _p in ['HBC', 'BCH', 'BHC']:
    G['t-store-perm-' + _p] = [("\n".join(_ST[c] for c in 'CHB'), "\n".join(_ST[c] for c in _p))]
