# w13a34-cto-newknobs: new semantics-preserving spellings outside the frame/validate regions of admin_cto::execute.
# Each knob: list of exact (old,new) replacements with equal newline counts. Strings are against main 06e6bb829.
K={}
EVA="authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),"
K['ev_mint_key']=[(EVA,"authority:a.admin_set_creator_authority.key(),mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),")]
K['ev_auth_deref']=[(EVA,"authority:*a.admin_set_creator_authority.key,mint,bonding_curve:a.bonding_curve.key(),")]
K['ev_newfee_unwrap']=[("new_creator_fee_bps:a.bonding_curve.creator_fee_bps,","new_creator_fee_bps:fee.unwrap_or(old_fee),")]
K['ev_reset_shared']=[("sharing_config_reset:sharing_update.is_some(),","sharing_config_reset:shared,")]
K['ev_nc_target']=[("new_creator:a.bonding_curve.creator,","new_creator:target,")]
K['ev_cb_local']=[("is_cashback_coin:a.bonding_curve.is_cashback_coin,","is_cashback_coin:cashback,")]
K['ev_hr_curve']=[("is_holder_reward:holder,is_cashback_coin","is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin")]
EVT="let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,"
K['ev_ts_clockvar']=[(EVT,"let clock=Clock::get()?;let e=AdminCtoEvent{timestamp:clock.unix_timestamp,")]
K['ev_ts_map']=[(EVT,"let e=AdminCtoEvent{timestamp:Clock::get().map(|c|c.unix_timestamp)?,")]
PU="let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();"
K['ev_ts_prepool']=[(EVT,"let e=AdminCtoEvent{timestamp:ts,"),(PU,"let ts=Clock::get()?.unix_timestamp;"+PU)]
SIG='let signer_seeds:&[&[&[u8]]]=&[&[b"pool-authority",mint.as_ref(),&[ctx.bumps.pool_authority]]];'
K['ev_ts_presig']=[(EVT,"let e=AdminCtoEvent{timestamp:ts,"),(SIG,"let ts=Clock::get()?.unix_timestamp;"+SIG)]
K['pu_amm_key']=[(PU,"let pool_updated=a.pool.owner==a.pump_amm.key && !a.pool.data_is_empty();")]
K['pu_amm_keyfn']=[(PU,"let pool_updated=*a.pool.owner==a.pump_amm.key() && !a.pool.data_is_empty();")]
K['sh_fees_key']=[("a.sharing_config.owner==&FEES","a.sharing_config.owner==a.pump_fees.key")]
K['sig_mint_acct']=[(SIG,SIG.replace("mint.as_ref(),","a.mint.key.as_ref(),"))]
PC0="crate::pump_amm::cpi::admin_cto_pool(CpiContext::new_with_signer(a.pump_amm.to_account_info(),crate::pump_amm::cpi::accounts::AdminCtoPool{"
PC1="},signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;"
K['pool_accs_let']=[(PC0,"let accs=crate::pump_amm::cpi::accounts::AdminCtoPool{"),(PC1,"};crate::pump_amm::cpi::admin_cto_pool(CpiContext::new_with_signer(a.pump_amm.to_account_info(),accs,signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;")]
K['pool_prog_let']=[(PC0,"let prog=a.pump_amm.to_account_info();"+PC0.replace("a.pump_amm.to_account_info(),crate::pump_amm::cpi::accounts","prog,crate::pump_amm::cpi::accounts"))]
K['pool_hr_local']=[(PC1,"},signer_seeds),target,holder,fee)?;")]
K['pool_tgt_curve']=[(PC1,"},signer_seeds),a.bonding_curve.creator,a.bonding_curve.is_holder_reward,fee)?;")]
SC0="crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{"
SC1="}},signer_seeds),val)?;"
K['sh_accs_let']=[(SC0,"let accs=crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{"),(SC1,"}};crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),accs,signer_seeds),val)?;")]
K['sh_prog_let']=[(SC0,"let prog=a.pump_fees.to_account_info();"+SC0.replace("a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts","prog,crate::pump_fees::cpi::accounts"))]
K['cu_replace']=[("let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;","let old_creator=core::mem::replace(&mut curve.creator,target);let old_fee=curve.creator_fee_bps;"),("  curve.creator=target;\n","\n")]
K['cu_typed']=[("let curve=&mut ctx.accounts.bonding_curve;","let curve:&mut BondingCurve=&mut ctx.accounts.bonding_curve;")]
K['cu_fee_oldunwrap']=[("if let Some(f)=fee{curve.creator_fee_bps=f;}","curve.creator_fee_bps=fee.unwrap_or(old_fee);")]
K['rent_map']=[("let min=Rent::get()?.minimum_balance(0);","let min=Rent::get().map(|r|r.minimum_balance(0))?;")]
WT="let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,"
K['wl_ts_map']=[(WT,"let e=CollectCreatorFeeEvent{timestamp:Clock::get().map(|c|c.unix_timestamp)?,")]
K['wl_ts_clockvar']=[(WT,"let clock=Clock::get()?;let e=CollectCreatorFeeEvent{timestamp:clock.unix_timestamp,")]
K['tail_a_ctx']=[(" let a=&ctx.accounts;\n let pool_updated"," let a=&*ctx.accounts;\n let pool_updated")]
# --- batch 3 ---
K['sig_arr']=[(SIG,SIG.replace("let signer_seeds:&[&[&[u8]]]=","let signer_seeds:&[&[&[u8]];1]="))]
K['pu_match']=[(" if pool_updated{\n"," match pool_updated{true=>{\n"),(" }else{msg!(\"No canonical pump pool for this mint; curve only\");}"," }false=>{msg!(\"No canonical pump pool for this mint; curve only\");}}")]
K['pu_len']=[(PU,"let pool_updated=a.pool.owner==&AMM && a.pool.data_len()!=0;")]
K['cu_fee_replace']=[("let old_fee=curve.creator_fee_bps;","let old_fee=match fee{Some(f)=>core::mem::replace(&mut curve.creator_fee_bps,f),None=>curve.creator_fee_bps};"),("  if let Some(f)=fee{curve.creator_fee_bps=f;}\n","\n")]
K['wl_cr_deref']=[("creator:a.current_creator.key(),creator_fee:collected","creator:*a.current_creator.key,creator_fee:collected")]
K['rent_checked']=[("let amount=a.creator_vault.lamports().saturating_sub(min);","let amount=a.creator_vault.lamports().checked_sub(min).unwrap_or(0);")]
K['pool_args_pre']=[(PU,PU+"let pargs=(target,a.bonding_curve.is_holder_reward,fee);"),(PC1,"},signer_seeds),pargs.0,pargs.1,pargs.2)?;")]
K['ev_nf_pre']=[(PU,"let nf=a.bonding_curve.creator_fee_bps;"+PU),("new_creator_fee_bps:a.bonding_curve.creator_fee_bps,","new_creator_fee_bps:nf,")]
K['ev_nc_pre']=[(PU,"let nc=a.bonding_curve.creator;"+PU),("new_creator:a.bonding_curve.creator,","new_creator:nc,")]
K['ev_auth_pre']=[(PU,"let auth=a.admin_set_creator_authority.key();"+PU),(EVA,"authority:auth,mint,bonding_curve:a.bonding_curve.key(),")]
K['ev_bc_pre']=[(PU,"let bck=a.bonding_curve.key();"+PU),(EVA,"authority:a.admin_set_creator_authority.key(),mint,bonding_curve:bck,")]
K['ev_cb_pre']=[(PU,"let cbc=a.bonding_curve.is_cashback_coin;"+PU),("is_cashback_coin:a.bonding_curve.is_cashback_coin,","is_cashback_coin:cbc,")]
# --- reset family (ev_reset_shared = -128 B, +0.0032 on 06e6bb8) ---
RS="sharing_config_reset:sharing_update.is_some(),"
K['rs_presig']=[(SIG,"let reset=shared;"+SIG),(RS,"sharing_config_reset:reset,")]
K['rs_after_tree']=[("let mut target=target; crate::trade_types::prepare_bonding_curve","let mut target=target;let reset=sharing_update.is_some(); crate::trade_types::prepare_bonding_curve"),(RS,"sharing_config_reset:reset,")]
K['rs_notnone']=[(RS,"sharing_config_reset:!matches!(sharing_update,None),")]
K['rs_top']=[("let holder_key;let hk=","let reset=shared;let holder_key;let hk="),(RS,"sharing_config_reset:reset,")]
K['rs_prepool']=[(PU,"let reset=shared;"+PU),(RS,"sharing_config_reset:reset,")]
K['rs_iflet']=[(RS,"sharing_config_reset:if let Some(_)=sharing_update{true}else{false},")]
