# Round-1 genes over main 917ee615 admin_cto.rs. Each gene: list of (old, new), same newline count.
SHARED = "let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();"
QL = "let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);"
HK = "let (holder_key,_)=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);"
HOLDER = "let holder=holder==Some(true);"
CB = "let cashback=!holder&&st.cashback;"
VAL = "let mut target=validate(&st,holder,fee,new,holder_key,a.sharing_config.key())?;"
SU = "let sharing_update=if shared{Some(if holder{None}else{new})}else{None};"
CO = "let collect_old=sharing_update.is_none()&&!st.holder_reward&&st.creator!=Pubkey::default();"
TO = "if shared&&!holder{target=st.creator;}"
PREP = "crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;"
REQ410 = " require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);"

GENES = {
    # --- execute prologue order ---
    'ql_before_shared': [(SHARED + QL, QL + SHARED)],
    'hk_after_shared': [(HK + SHARED, SHARED + HK)],
    'hk_after_ql': [(HK + SHARED + QL, SHARED + QL + HK)],
    'mint_inline_hk': [("let mint=a.mint.key();" + HK, HK.replace('mint.as_ref()', 'a.mint.key().as_ref()') + "let mint=a.mint.key();")],
    'shared_owner_first': [(SHARED, "let shared=a.sharing_config.owner==&FEES&&a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty();")],
    'shared_empty_first': [(SHARED, "let shared=!a.sharing_config.data_is_empty()&&a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES;")],
    'shared_key_lhs': [(SHARED, "let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();")],
    'shared_bitand': [(SHARED, "let shared=(a.bonding_curve.creator==a.sharing_config.key())&(a.sharing_config.owner==&FEES)&!a.sharing_config.data_is_empty();")],
    'ql_inline_ctostate': [(QL, ""), ("quote_locked,holder_enabled", "quote_locked:crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global),holder_enabled")],
    'a_deref': [("pub fn execute(ctx:Context<AdminCto>,holder:Option<bool>,fee:Option<u64>,new:Option<Pubkey>)->Result<()>{ let a=&ctx.accounts;",
                 "pub fn execute(ctx:Context<AdminCto>,holder:Option<bool>,fee:Option<u64>,new:Option<Pubkey>)->Result<()>{ let a=&*ctx.accounts;")],
    # --- holder / cashback forms ---
    'holder_unwrap_or': [(HOLDER, "let holder=holder.unwrap_or(false);")],
    'holder_matches': [(HOLDER, "let holder=matches!(holder,Some(true));")],
    'holder_is_some_and': [(HOLDER, "let holder=holder.is_some_and(|h|h);")],
    'holder_eq_true_ref': [(HOLDER, "let holder=holder==Some(true)&&true;")],
    'holder_before_st': [(HOLDER, ""), ("let (holder,cashback,target,sharing_update,collect_old)={let st=", HOLDER + "let (holder,cashback,target,sharing_update,collect_old)={let st=")],
    'cashback_after_validate': [(CB + VAL, VAL + CB)],
    'cashback_bitand': [(CB, "let cashback=!holder&st.cashback;")],
    'cashback_end': [(CB, ""), ("if shared&&!holder{target=st.creator;}(holder", "if shared&&!holder{target=st.creator;}" + CB + "(holder")],
    # --- validate signature / call ---
    'st_by_value': [("struct CtoState{", "#[derive(Clone,Copy)]struct CtoState{"), ("fn validate(st:&CtoState,", "fn validate(st:CtoState,"), ("validate(&st,", "validate(st,")],
    'validate_keys_ref': [("holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{", "holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{"),
                          ("holder_key}else{", "*holder_key}else{"), ("if t==holder_key||t==sharing{", "if t==*holder_key||t==*sharing{"),
                          ("new,holder_key,a.sharing_config.key())?", "new,&holder_key,a.sharing_config.key)?")],
    'validate_sharing_ref': [("holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{", "holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>{"),
                             ("if t==holder_key||t==sharing{", "if t==holder_key||t==*sharing{"),
                             ("new,holder_key,a.sharing_config.key())?", "new,holder_key,a.sharing_config.key)?")],
    'validate_or_order': [("if t==holder_key||t==sharing{", "if t==sharing||t==holder_key{")],
    'validate_zero_eq_rev': [("if t==Pubkey::default(){", "if Pubkey::default()==t{")],
    'fee_range_rev': [("if f==0||f>st.max_fee{", "if f>st.max_fee||f==0{")],
    'fee_range_contains': [("if f==0||f>st.max_fee{", "if !(1..=st.max_fee).contains(&f){")],
    'cashback_check_rev': [("if !holder&&st.cashback{", "if st.cashback&&!holder{")],
    'mayhem_match': [(" if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}", " if st.mayhem==true{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}")],
    'hr_check_rev': [("if st.holder_reward&&!holder{", "if !holder&&st.holder_reward{")],
    # --- sharing_update / collect_old / target override ---
    'su_match': [(SU, "let sharing_update=match (shared,holder){(true,true)=>Some(None),(true,false)=>Some(new),_=>None};")],
    'su_then': [(SU, "let sharing_update=shared.then(||if holder{None}else{new});")],
    'co_not_shared': [(CO, "let collect_old=!shared&&!st.holder_reward&&st.creator!=Pubkey::default();")],
    'co_reorder': [(CO, "let collect_old=st.creator!=Pubkey::default()&&!st.holder_reward&&sharing_update.is_none();")],
    'to_before_su': [(SU + CO + TO, TO + SU + CO)],
    'to_ifexpr': [(VAL, "let target=validate(&st,holder,fee,new,holder_key,a.sharing_config.key())?;"), (TO, "let target=if shared&&!holder{st.creator}else{target};")],
    'prep_after_410': [(PREP, ""), (REQ410, REQ410 + PREP)],
    # --- wallet ---
    'wallet_flag': [(" if collect_old{wallet(&ctx)?;}fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;",
                     " wallet(&ctx,collect_old)?;fn wallet(ctx:&Context<AdminCto>,go:bool)->Result<()>{if !go{return Ok(());}let a=&ctx.accounts;")],
    'wallet_deref': [("fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;", "fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&*ctx.accounts;")],
    # --- sweep ---
    'swept_ifexpr': [(" let mut swept=0;", ""), (" if shared && holder{swept=sweep(&ctx,&holder_key)?;}", " let swept=if shared && holder{sweep(&ctx,&holder_key)?}else{0};")],
    'swept_out': [(" if shared && holder{swept=sweep(&ctx,&holder_key)?;}fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{",
                   " if shared && holder{sweep(&ctx,&holder_key,&mut swept)?;}fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey,out:&mut u64)->Result<()>{"),
                  (" Ok(amount)}", " *out=amount;Ok(())}")],
    'swept_match': [(" if shared && holder{swept=sweep(&ctx,&holder_key)?;}", " if shared && holder{swept=match sweep(&ctx,&holder_key){Ok(v)=>v,Err(e)=>return Err(e)};}")],
    'sweep_hk_val': [("swept=sweep(&ctx,&holder_key)?;}fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)", "swept=sweep(&ctx,holder_key)?;}fn sweep(ctx:&Context<AdminCto>,holder_key:Pubkey)")],
    'sweep_gate_inside': [(" if shared && holder{swept=sweep(&ctx,&holder_key)?;}fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;",
                           " swept=sweep(&ctx,&holder_key,shared && holder)?;fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey,go:bool)->Result<u64>{if !go{return Ok(0);}let a=&ctx.accounts;")],
    'sweep_gate_rev': [(" if shared && holder{swept=", " if holder && shared{swept=")],
    'sweep_deref': [("->Result<u64>{let a=&ctx.accounts;", "->Result<u64>{let a=&*ctx.accounts;")],
    'sweep_native_late': [("->Result<u64>{let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;", "->Result<u64>{let a=&ctx.accounts;"),
                          ("let bump=[ctx.bumps.creator_vault];", "let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;let bump=[ctx.bumps.creator_vault];")],
    'sweep_coin_present': [("let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(", "let coin_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=coin_present&&token_frozen("),
                           ("else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm", "else if coin_present{crate::pump_amm")],
    'sweep_dest_ne_rev': [("if a.holder_creator_vault.key()!=dest{", "if dest!=a.holder_creator_vault.key(){")],
    'sweep_amount_gt0_ne': [("   if amount>0{crate::legacy_buy", "   if amount!=0{crate::legacy_buy")],
    'sweep_tok_amount_ne': [("else if amount>0{anchor_spl", "else if amount!=0{anchor_spl")],
    'sweep_frozen_first': [("let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;",
                            "let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;")],
    # --- post-sweep ---
    'su_iflet_match': [(" if let Some(val)=sharing_update{", " match sharing_update{Some(val)=>{"), (" }\n let (old_creator", " }None=>{}}\n let (old_creator")],
    'pool_order': [("let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", "let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;")],
    'pool_key_eq': [("let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", "let pool_updated=*a.pool.owner==AMM && !a.pool.data_is_empty();")],
    'fee_unwrap_or': [("  if let Some(f)=fee{curve.creator_fee_bps=f;}", "  curve.creator_fee_bps=fee.unwrap_or(old_fee);")],
    'curve_swap_754_755': [("  curve.creator=target;\n  curve.is_holder_reward=holder;", "  curve.is_holder_reward=holder;\n  curve.creator=target;")],
    'curve_swap_755_756': [("  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;", "  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;")],
    'curve_edit_first': [("  curve.creator=target;", "  curve.can_edit_creator_fee=false;curve.creator=target;"), ("  curve.can_edit_creator_fee=false;\n (old", "\n (old")],
    'ev_new_creator_local': [("new_creator:a.bonding_curve.creator,", "new_creator:target,")],
    'ev_flags_local': [("is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,", "is_holder_reward:holder,is_cashback_coin:cashback,")],
    'ev_su_flag_early': [(" let pb=[ctx.bumps.pool_authority];", " let reset=sharing_update.is_some();let pb=[ctx.bumps.pool_authority];"), ("sharing_config_reset:sharing_update.is_some(),", "sharing_config_reset:reset,")],
    'ev_clock_first': [(" let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,", " let ts=Clock::get()?.unix_timestamp;let e=AdminCtoEvent{timestamp:ts,")],
    'a_reborrow_drop': [(" let a=&ctx.accounts;\n let pool_updated", " let a=&*ctx.accounts;\n let pool_updated")],
    'seeds_after_su': [(" let pb=[ctx.bumps.pool_authority];let poolseeds:&[&[u8]]=&[b\"pool-authority\",mint.as_ref(),&pb];let signer_seeds:&[&[&[u8]]]=&[poolseeds];",
                        " let pb=[ctx.bumps.pool_authority];let signer_seeds:&[&[&[u8]]]=&[&[b\"pool-authority\",mint.as_ref(),&pb]];")],
}
