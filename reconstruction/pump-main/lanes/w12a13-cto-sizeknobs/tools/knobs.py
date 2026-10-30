# Size knobs: small, ordinary, semantics-preserving single edits to admin_cto.rs (same lines, same error sites).
# Each knob is a list of (old, new) pairs; every old must occur exactly once in the base text.
K = {}
# ---------------- execute prologue (line 339) ----------------
K['hk_dot0'] = [("let (holder_key,_)=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);",
                 "let holder_key=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID).0;")]
K['sh_owner_deref'] = [("a.sharing_config.owner==&FEES", "*a.sharing_config.owner==FEES")]
K['sh_key_borrow'] = [("let shared=a.bonding_curve.creator==a.sharing_config.key()&&", "let shared=a.bonding_curve.creator==*a.sharing_config.key&&")]
K['sh_key_rev'] = [("let shared=a.bonding_curve.creator==a.sharing_config.key()&&", "let shared=a.sharing_config.key()==a.bonding_curve.creator&&")]
K['sh_owner_first'] = [("let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();",
                        "let shared=a.sharing_config.owner==&FEES&&a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty();")]
K['sh_empty_mid'] = [("let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();",
                      "let shared=a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty()&&a.sharing_config.owner==&FEES;")]
K['hold_matches'] = [("let holder=holder==Some(true);", "let holder=matches!(holder,Some(true));")]
K['hold_unwrap'] = [("let holder=holder==Some(true);", "let holder=holder.unwrap_or(false);")]
K['hold_rev'] = [("let holder=holder==Some(true);", "let holder=Some(true)==holder;")]
K['cb_rev'] = [("let cashback=!holder&&st.cashback;", "let cashback=st.cashback&&!holder;")]
K['cb_bitand'] = [("let cashback=!holder&&st.cashback;", "let cashback=!holder&st.cashback;")]
K['val_sh_borrow'] = [("&holder_key,&a.sharing_config.key())?;", "&holder_key,a.sharing_config.key)?;")]
K['val_match'] = [("let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;",
                   "let mut target=match validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key()){Ok(t)=>t,Err(e)=>return Err(e)};")]
K['tgt_shadow_drop'] = [("};let mut target=target; crate::trade_types", "}; crate::trade_types")]
K['prep_match'] = [("crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;",
                    "if let Err(e)=crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority){return Err(e);}")]
K['st_ql_first'] = [("let st=CtoState{creator:a.bonding_curve.creator,", "let st=CtoState{quote_locked,creator:a.bonding_curve.creator,"),
                    ("cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled", "cashback:a.bonding_curve.is_cashback_coin,holder_enabled")]
K['st_global_first'] = [("let st=CtoState{creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled,fee_configurable:a.global.creator_fee_configurable};",
                         "let st=CtoState{max_fee:a.global.max_configurable_creator_fee_bps,holder_enabled:a.global.is_holder_reward_enabled,fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked};")]
# ---------------- validate ----------------
K['v_mayhem_req'] = [("if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}", "require!(!st.mayhem,PumpError::CtoNotAllowedForMayhemCoin);")]
K['v_hr_rev'] = [("if st.holder_reward&&!holder{", "if !holder&&st.holder_reward{")]
K['v_he_demorgan'] = [("if holder&&!st.holder_reward&&!st.holder_enabled{", "if holder&&!(st.holder_reward||st.holder_enabled){")]
K['v_new_match'] = [("let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};",
                     "let t=match new{Some(t)=>t,None=>return Err(error!(PumpError::CtoNewCreatorRequired))};")]
K['v_new_okor'] = [("let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};",
                    "let t=new.ok_or_else(||error!(PumpError::CtoNewCreatorRequired))?;")]
K['v_ik_split'] = [("if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}",
                    "if t==*holder_key{return Err(error!(PumpError::InvalidCreator));}if t==*sharing{return Err(error!(PumpError::InvalidCreator));}")]
K['v_ik_rev'] = [("if t==*holder_key||t==*sharing{", "if t==*sharing||t==*holder_key{")]
K['v_ik_borrow'] = [("if t==*holder_key||t==*sharing{", "if &t==holder_key||&t==sharing{")]
K['v_fee_split'] = [("if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}",
                     "if f==0{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}if f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}")]
K['v_fee_range'] = [("if f==0||f>st.max_fee{", "if !(1..=st.max_fee).contains(&f){")]
K['v_cb_rev'] = [("if !holder&&st.cashback{", "if st.cashback&&!holder{")]
K['v_new_issome'] = [("if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}", "if let Some(_)=new{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}")]
# ---------------- wallet ----------------
K['w_owner_deref'] = [("a.current_creator.owner!=&anchor_lang::system_program::ID", "*a.current_creator.owner!=anchor_lang::system_program::ID")]
K['w_writable_req'] = [("if !a.current_creator.is_writable{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}",
                        "require!(a.current_creator.is_writable,PumpError::CtoCreatorAccountNotWritable);")]
K['w_native_rev'] = [("let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;",
                      "let collection_native=anchor_spl::token::spl_token::native_mint::ID==a.quote_mint.key();")]
K['w_frozen_match'] = [("if token_frozen(a.current_creator_quote_token_account.as_ref())?{",
                        "if match token_frozen(a.current_creator_quote_token_account.as_ref()){Ok(f)=>f,Err(e)=>return Err(e)}{")]
K['w_create_rev'] = [("anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.current_creator_quote_token_account.to_account_info(),authority:a.current_creator.to_account_info(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()}",
                      "anchor_spl::associated_token::Create{token_program:a.quote_token_program.to_account_info(),system_program:a.system_program.to_account_info(),mint:a.quote_mint.to_account_info(),authority:a.current_creator.to_account_info(),associated_token:a.current_creator_quote_token_account.to_account_info(),payer:a.admin_set_creator_authority.to_account_info()}")]
K['w_ev_creator_first'] = [("CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:a.current_creator.key(),",
                            "CollectCreatorFeeEvent{creator:a.current_creator.key(),timestamp:Clock::get()?.unix_timestamp,")]
K['w_ev_creator_borrow'] = [("creator:a.current_creator.key(),creator_fee:collected", "creator:*a.current_creator.key,creator_fee:collected")]
K['w_ev_ts_let'] = [("let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,", "let timestamp=Clock::get()?.unix_timestamp;let e=CollectCreatorFeeEvent{timestamp,")]
K['w_coin_cpi_rev'] = [("crate::pump_amm::cpi::accounts::CollectCoinCreatorFee{quote_mint:a.quote_mint.to_account_info(),quote_token_program:a.quote_token_program.to_account_info(),coin_creator:a.current_creator.to_account_info(),coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),coin_creator_vault_ata:a.coin_creator_vault_ata.to_account_info(),coin_creator_token_account:a.current_creator_quote_token_account.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()}",
                        "crate::pump_amm::cpi::accounts::CollectCoinCreatorFee{program:a.pump_amm.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),coin_creator_token_account:a.current_creator_quote_token_account.to_account_info(),coin_creator_vault_ata:a.coin_creator_vault_ata.to_account_info(),coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),coin_creator:a.current_creator.to_account_info(),quote_token_program:a.quote_token_program.to_account_info(),quote_mint:a.quote_mint.to_account_info()}")]
K['w_coin_cpi_match'] = [("program:a.pump_amm.to_account_info()}))?;}\n }}Ok(())}", "program:a.pump_amm.to_account_info()})).map_err(|e|e)?;}\n }}Ok(())}")]
# ---------------- sweep ----------------
K['s_native_rev'] = [("let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;", "let native=anchor_spl::token::spl_token::native_mint::ID==a.quote_mint.key();")]
K['s_dest_tuple'] = [("let dest=Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID).0;",
                      "let (dest,_)=Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID);")]
K['s_dest_borrow'] = [("if a.holder_creator_vault.key()!=dest{", "if *a.holder_creator_vault.key!=dest{")]
K['s_dest_rev'] = [("if a.holder_creator_vault.key()!=dest{", "if dest!=a.holder_creator_vault.key(){")]
K['s_amm_let'] = [("if amm_frozen{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}",
                   "if amm_frozen{let left=token_raw_amount(a.coin_creator_vault_ata.as_ref())?;require!(left==0,PumpError::CtoSharedVaultFrozen);}")]
K['s_old_borrow'] = [("let old=a.current_creator.key();", "let old=a.current_creator.key;")]
K['s_bump_inline'] = [("let bump=[ctx.bumps.creator_vault];let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&bump];",
                       "let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&[ctx.bumps.creator_vault]];")]
K['s_rent_local'] = [("let min=Rent::get()?.minimum_balance(0);", "let rent=Rent::get()?;let min=rent.minimum_balance(0);")]
K['s_amt_ne'] = [("if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt", "if amount!=0{crate::legacy_buy::native_payments::ensure_rent_exempt")]
K['s_satsub'] = [("a.creator_vault.lamports().saturating_sub(min)", "a.creator_vault.lamports().checked_sub(min).unwrap_or(0)")]
K['s_tok_ne'] = [("else if amount>0{anchor_spl::associated_token::create_idempotent", "else if amount!=0{anchor_spl::associated_token::create_idempotent")]
K['s_tok_amt_match'] = [("let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;",
                         "let amount=match token_raw_amount(a.creator_vault_quote_token_account.as_ref()){Ok(v)=>v,Err(e)=>return Err(e)};")]
K['s_ensure_match'] = [("crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;",
                        "if let Err(e)=crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault){return Err(e);}")]
K['s_tok_create_rev'] = [("anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.holder_creator_vault_quote_token_account.to_account_info(),authority:a.holder_creator_vault.to_account_info(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()}",
                          "anchor_spl::associated_token::Create{token_program:a.quote_token_program.to_account_info(),system_program:a.system_program.to_account_info(),mint:a.quote_mint.to_account_info(),authority:a.holder_creator_vault.to_account_info(),associated_token:a.holder_creator_vault_quote_token_account.to_account_info(),payer:a.admin_set_creator_authority.to_account_info()}")]
K['s_tcf_rev'] = [("TransferCreatorFeesToPumpV2{system_program:a.system_program.to_account_info(),quote_mint:a.quote_mint.to_account_info(),token_program:a.quote_token_program.to_account_info(),payer:a.admin_set_creator_authority.to_account_info(),associated_token_program:a.associated_token_program.to_account_info(),coin_creator:a.current_creator.to_account_info(),coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),coin_creator_vault_ata:a.coin_creator_vault_ata.to_account_info(),pump_creator_vault:a.creator_vault.to_account_info(),pump_creator_vault_ata:a.creator_vault_quote_token_account.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()}",
                   "TransferCreatorFeesToPumpV2{program:a.pump_amm.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),pump_creator_vault_ata:a.creator_vault_quote_token_account.to_account_info(),pump_creator_vault:a.creator_vault.to_account_info(),coin_creator_vault_ata:a.coin_creator_vault_ata.to_account_info(),coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),coin_creator:a.current_creator.to_account_info(),associated_token_program:a.associated_token_program.to_account_info(),payer:a.admin_set_creator_authority.to_account_info(),token_program:a.quote_token_program.to_account_info(),quote_mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info()}")]
K['s_amm_empty_let'] = [("let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(a.coin_creator_vault_ata.as_ref())?;",
                         "let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;")]
# ---------------- post-sweep ----------------
K['p_pb_inline'] = [("let pb=[ctx.bumps.pool_authority];let poolseeds:&[&[u8]]=&[b\"pool-authority\",mint.as_ref(),&pb];",
                     "let poolseeds:&[&[u8]]=&[b\"pool-authority\",mint.as_ref(),&[ctx.bumps.pool_authority]];")]
K['p_share_match'] = [(" if let Some(val)=sharing_update{\n", " match sharing_update{Some(val)=>{\n"),
                      ("signer_seeds),val)?;\n\n }\n", "signer_seeds),val)?;\n\n }None=>{}}\n")]
K['p_share_ref'] = [(" if let Some(val)=sharing_update{\n", " if let Some(val)=&sharing_update{\n"), ("signer_seeds),val)?;\n", "signer_seeds),*val)?;\n")]
K['p_pool_owner_deref'] = [("a.pool.owner==&AMM", "*a.pool.owner==AMM")]
K['p_pool_with_signer'] = [("admin_cto_pool(CpiContext::new_with_signer(", "admin_cto_pool(CpiContext::new("),
                           ("program:a.pump_amm.to_account_info()},signer_seeds),target,holder,fee)?;", "program:a.pump_amm.to_account_info()}).with_signer(signer_seeds),target,holder,fee)?;")]
K['p_ev_ts_let'] = [("let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,", "let timestamp=Clock::get()?.unix_timestamp;let e=AdminCtoEvent{timestamp,")]
K['p_ev_auth_borrow'] = [("authority:a.admin_set_creator_authority.key(),", "authority:*a.admin_set_creator_authority.key,")]
K['p_ev_mint_first'] = [("let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,authority:a.admin_set_creator_authority.key(),mint,",
                         "let e=AdminCtoEvent{mint,timestamp:Clock::get()?.unix_timestamp,authority:a.admin_set_creator_authority.key(),")]
K['p_ev_ts_last'] = [("let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,authority:a.admin_set_creator_authority.key(),", "let e=AdminCtoEvent{authority:a.admin_set_creator_authority.key(),"),
                     ("swept_to_holder_vault:swept,pool_updated};", "swept_to_holder_vault:swept,pool_updated,timestamp:Clock::get()?.unix_timestamp};")]
K['p_pool_match'] = [("signer_seeds),target,holder,fee)?;\n", "signer_seeds),target,holder,fee).map_err(|e|e)?;\n")]
K['p_ctx_a_reborrow'] = [(" let a=&ctx.accounts;\n let pool_updated", " let a=&*ctx.accounts;\n let pool_updated")]
# ---------------- main-only knobs (regions the k4 genes rewrite) ----------------
K['m_su_then'] = [("let sharing_update=if shared{Some(if holder{None}else{new})}else{None};", "let sharing_update=shared.then(||if holder{None}else{new});")]
K['m_co_order'] = [("let collect_old=!shared&&!st.holder_reward&&st.creator!=Pubkey::default();", "let collect_old=!st.holder_reward&&!shared&&st.creator!=Pubkey::default();")]
K['m_target_if_rev'] = [("if shared&&!holder{target=st.creator;}", "if !holder&&shared{target=st.creator;}")]
K['m_src_frozen_short'] = [("let source_frozen=!collection_native&&source_present&&token_frozen(", "let source_frozen=source_present&&token_frozen(")]
K['m_coin_first'] = [("let coin_present=!a.coin_creator_vault_ata.data_is_empty();let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();\n  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;\n  let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;",
                      "let coin_present=!a.coin_creator_vault_ata.data_is_empty();let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();\n  let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;\n  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;")]
K['s_frozen_first'] = [("let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;",
                        "let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;")]
K['p_pool_empty_first'] = [(" let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", " let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;")]
K['p_hr_before_creator'] = [("  curve.creator=target;\n  curve.is_holder_reward=holder;\n", "  curve.is_holder_reward=holder;\n  curve.creator=target;\n")]
K['p_cb_before_hr'] = [("  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n", "  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;\n")]
K['g_fee_unwrap'] = [("  if let Some(f)=fee{curve.creator_fee_bps=f;}\n", "  curve.creator_fee_bps=fee.unwrap_or(old_fee);\n")]
K['g_canedit_first'] = [("let old_fee=curve.creator_fee_bps;\n  curve.creator=target;", "let old_fee=curve.creator_fee_bps;curve.can_edit_creator_fee=false;\n  curve.creator=target;"),
                        ("  curve.can_edit_creator_fee=false;\n (old_creator", "\n (old_creator")]
K['g_old_fee_first'] = [("let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;", "let old_fee=curve.creator_fee_bps;let old_creator=curve.creator;")]
K['g_region2_tree'] = [("let sharing_update=if shared{Some(if holder{None}else{new})}else{None};let collect_old=!shared&&!st.holder_reward&&st.creator!=Pubkey::default();if shared&&!holder{target=st.creator;}",
                        "let (sharing_update,collect_old)=if shared{if holder{(Some(None),false)}else{target=st.creator;(Some(new),false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default())};")]
K['s_bump_first'] = [("let old=a.current_creator.key();let bump=[ctx.bumps.creator_vault];", "let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();")]
# ---------------- L1-only variants (L1 binds bump before old) ----------------
K['L_bump_inline'] = [("let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&bump];",
                       "let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&[ctx.bumps.creator_vault]];")]
K['L_share_none_first'] = [(" match sharing_update{Some(val)=>{\n", " match sharing_update{None=>{}Some(val)=>{\n"), ("signer_seeds),val)?;\n\n }None=>{}}\n", "signer_seeds),val)?;\n\n }}\n")]
