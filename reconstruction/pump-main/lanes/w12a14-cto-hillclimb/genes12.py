# Lane w12a14-cto-hillclimb gene library over main 20a1ae9c0 admin_cto.rs.
# Each gene: list of exact (old, new) substitutions with equal newline counts (error-site lines fixed).
P_A = " let a=&ctx.accounts;let mint=a.mint.key();"
HK = 'let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'
SHARED = "let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();"
QL = "let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);"
BLK = "let (holder,cashback,target,sharing_update,collect_old)={"
ST = "let st=CtoState{creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled,fee_configurable:a.global.creator_fee_configurable}; "
HOLDER = "let holder=holder==Some(true);"
CB = "let cashback=!holder&&st.cashback;"
VAL = "let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;"
SU = "let sharing_update=if shared{Some(if holder{None}else{new})}else{None};"
CO = "let collect_old=!shared&&!st.holder_reward&&st.creator!=Pubkey::default();"
TO = "if shared&&!holder{target=st.creator;}"
BLKC = "(holder,cashback,target,sharing_update,collect_old)};let mut target=target;"
PREP = " crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;"
VSIG = "fn validate(st:&CtoState,holder:bool,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{"
L289 = " if st.holder_reward&&!holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}"
L296 = " if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}"
L298 = " let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"
L306 = "  let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};"
L307 = "  if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}"
L312 = "  if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}t};"
L326 = " if let Some(f)=fee{if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}"
L330 = "  if !holder&&st.cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}"
L334 = "  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}"
L338 = "  if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}"
W0 = " if collect_old{wallet(&ctx)?;}fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;"
WEXE = 'if a.current_creator.executable{msg!("Creator is a program; fees left in the vaults");}else if a.current_creator.owner!=&anchor_lang::system_program::ID{msg!("Creator is not a system-owned wallet; fees left in the vaults");}else{'
WWR = "if !a.current_creator.is_writable{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}"
WFZ = 'if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!("Creator quote token account is frozen; fees left in the vaults");}else{'
W557 = "  let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;"
W558 = "  let coin_present=!a.coin_creator_vault_ata.data_is_empty();let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();"
W559 = "  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;"
W560 = "  let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;"
W561 = "  if !collection_native||coin_present{anchor_spl::associated_token::create_idempotent("
W562 = "  if collection_native||(source_present&&!source_frozen){"
W563 = "    if let Some((collected,quote_mint))=crate::collect_v2::collect("
W567 = "  if coin_present&&!coin_frozen{"
SW0 = " swept=(shared&&holder).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;"
NAT = "let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;"
DEST = '  let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;'
DESTCHK = "if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}"
AMMF = "  let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(a.coin_creator_vault_ata.as_ref())?;"
L660 = "  if amm_frozen{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}"
L661 = "  else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2("
SEEDS = '  let old=a.current_creator.key();let bump=[ctx.bumps.creator_vault];let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];'
NARM = "  if native{let min=Rent::get()?.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);"
NARM2 = "   if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&[vaultseeds]).map(|()|amount)}else{Ok(amount)}}else{let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;"
L719 = "   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{anchor_spl::associated_token::create_idempotent("
SEED2 = ' let pb=[ctx.bumps.pool_authority];let poolseeds:&[&[u8]]=&[b"pool-authority",mint.as_ref(),&pb];let signer_seeds:&[&[&[u8]]]=&[poolseeds];'
SUIF = " if let Some(val)=sharing_update{"
SUCPI_END = "program:a.pump_fees.to_account_info()},signer_seeds),val)?;"
CURVE = "  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;"
POOL = " let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();"
EV = " let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,old_creator_fee_bps:old_fee,new_creator_fee_bps:a.bonding_curve.creator_fee_bps,sharing_config_reset:sharing_update.is_some(),swept_to_holder_vault:swept,pool_updated};"

GENES = {
    # ---------- k4 components (w9r2-admincto-harvest) ----------
    'wallet_flags': [(W558 + "\n" + W559 + "\n" + W560,
                      "  let coin_present=!a.coin_creator_vault_ata.data_is_empty();\n  let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);\n  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;"),
                     ("\n" + W562, "\n  if do_collect{"), ("\n" + W567, "\n  if do_coin{")],
    'region2_tree': [(SU + CO + TO, "let (sharing_update,collect_old)=if shared{if holder{(Some(None),false)}else{target=st.creator;(Some(new),false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default())};")],
    'fee_unwrap': [("  if let Some(f)=fee{curve.creator_fee_bps=f;}\n", "  curve.creator_fee_bps=fee.unwrap_or(old_fee);\n")],
    'canedit_first': [("let old_fee=curve.creator_fee_bps;\n  curve.creator=target;", "let old_fee=curve.creator_fee_bps;curve.can_edit_creator_fee=false;\n  curve.creator=target;"),
                      ("  curve.can_edit_creator_fee=false;\n (old_creator", "\n (old_creator")],
    'old_fee_first': [("let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;", "let old_fee=curve.creator_fee_bps;let old_creator=curve.creator;")],
    # ---------- prologue order / forms ----------
    'ql_before_shared': [(SHARED + QL, QL + SHARED)],
    'hk_after_shared': [(HK + SHARED, SHARED + HK)],
    'hk_after_ql': [(HK + SHARED + QL, SHARED + QL + HK)],
    'mint_inline_hk': [("let mint=a.mint.key();" + HK, HK.replace('mint.as_ref()', 'a.mint.key().as_ref()') + "let mint=a.mint.key();")],
    'hk_dot0': [(HK, 'let holder_key=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID).0;')],
    'shared_owner_first': [(SHARED, "let shared=a.sharing_config.owner==&FEES&&a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty();")],
    'shared_empty_first': [(SHARED, "let shared=!a.sharing_config.data_is_empty()&&a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES;")],
    'shared_key_lhs': [(SHARED, "let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();")],
    'shared_nested': [(SHARED, "let shared=if a.bonding_curve.creator==a.sharing_config.key(){a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()}else{false};")],
    'shared_owner_deref': [(SHARED, "let shared=a.bonding_curve.creator==a.sharing_config.key()&&*a.sharing_config.owner==FEES&&!a.sharing_config.data_is_empty();")],
    'ql_inline_st': [(QL, ""), ("quote_locked,holder_enabled", "quote_locked:crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global),holder_enabled")],
    'a_deref': [(P_A, " let a=&*ctx.accounts;let mint=a.mint.key();")],
    'holder_before_blk': [(HOLDER, ""), (BLK, HOLDER + BLK)],
    'holder_matches': [(HOLDER, "let holder=matches!(holder,Some(true));")],
    'holder_is_some_and': [(HOLDER, "let holder=holder.is_some_and(|h|h);")],
    'holder_match': [(HOLDER, "let holder=match holder{Some(h)=>h,None=>false};")],
    'holder_iflet': [(HOLDER, "let holder=if let Some(h)=holder{h}else{false};")],
    'holder_unwrap_or': [(HOLDER, "let holder=holder.unwrap_or(false);")],
    'cashback_after_validate': [(CB + VAL, VAL + CB)],
    'cashback_bitand': [(CB, "let cashback=!holder&st.cashback;")],
    'cashback_rev': [(CB, "let cashback=st.cashback&&!holder;")],
    'st_by_value': [("struct CtoState{", "#[derive(Clone,Copy)]struct CtoState{"), ("fn validate(st:&CtoState,", "fn validate(st:CtoState,"), ("validate(&st,", "validate(st,")],
    'val_match': [(VAL, "let mut target=match validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key()){Ok(t)=>t,Err(e)=>return Err(e)};")],
    'val_keys_value': [("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{", "holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{"),
                       ("{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{", "{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}holder_key}else{"),
                       ("if t==*holder_key||t==*sharing{", "if t==holder_key||t==sharing{"),
                       ("new,&holder_key,&a.sharing_config.key())", "new,holder_key,a.sharing_config.key())")],
    'val_sharing_value': [("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{", "holder_key:&Pubkey,sharing:Pubkey)->Result<Pubkey>{"),
                          ("if t==*holder_key||t==*sharing{", "if t==*holder_key||t==sharing{"),
                          ("new,&holder_key,&a.sharing_config.key())", "new,&holder_key,a.sharing_config.key())")],
    'val_new_ref': [("fee:Option<u64>,new:Option<Pubkey>,holder_key", "fee:Option<u64>,new:&Option<Pubkey>,holder_key"),
                    ("if new.is_some(){", "if new.is_some(){"),
                    ("  let Some(t)=new else{", "  let Some(t)=*new else{"),
                    ("validate(&st,holder,fee,new,", "validate(&st,holder,fee,&new,")],
    'val_fee_ref': [("holder:bool,fee:Option<u64>,new", "holder:bool,fee:&Option<u64>,new"),
                    (" if let Some(f)=fee{if st.quote_locked", " if let Some(f)=*fee{if st.quote_locked"),
                    ("validate(&st,holder,fee,new,", "validate(&st,holder,&fee,new,")],
    'to_ifexpr': [(VAL, VAL.replace('let mut target', 'let target')), (TO, ""), (BLKC, "(holder,cashback,if shared&&!holder{st.creator}else{target},sharing_update,collect_old)};let mut target=target;")],
    'to_before_su': [(SU + CO + TO, TO + SU + CO)],
    'drop_mut_target': [(BLKC, "(holder,cashback,target,sharing_update,collect_old)};")],
    'su_match': [(SU, "let sharing_update=match (shared,holder){(true,true)=>Some(None),(true,false)=>Some(new),_=>None};")],
    'su_then': [(SU, "let sharing_update=shared.then(||if holder{None}else{new});")],
    'su_holder_first': [(SU, "let sharing_update=if !shared{None}else if holder{Some(None)}else{Some(new)};")],
    'co_reorder': [(CO, "let collect_old=st.creator!=Pubkey::default()&&!st.holder_reward&&!shared;")],
    'co_shared_last': [(CO, "let collect_old=!st.holder_reward&&st.creator!=Pubkey::default()&&!shared;")],
    'co_su_none': [(CO, "let collect_old=sharing_update.is_none()&&!st.holder_reward&&st.creator!=Pubkey::default();")],
    'prep_match': [(PREP, " match crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority){Ok(())=>{},Err(e)=>return Err(e)};")],
    'blk_flat': [(BLK + ST, ST), (BLKC, "")],
    # ---------- validate ----------
    'v289_rev': [(L289, " if !holder&&st.holder_reward{return Err(error!(PumpError::HolderRewardCreatorImmutable));}")],
    'v289_nested': [(L289, " if st.holder_reward{if !holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}")],
    'v296_nested': [(L296, " if holder{if !st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}}")],
    'v296_rev': [(L296, " if !st.holder_reward&&!st.holder_enabled&&holder{return Err(error!(PumpError::HolderRewardDisabled));}")],
    'v296_or': [(L296, " if holder&&!(st.holder_reward||st.holder_enabled){return Err(error!(PumpError::HolderRewardDisabled));}")],
    'n298_iflet': [("if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}", "if let Some(_)=new{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}")],
    'n298_notnone': [("if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}", "if !new.is_none(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}")],
    'n298_match': [(L298, " let target=match holder{true=>{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}false=>{"),
                   ("return Err(error!(PumpError::InvalidCreator));}t};", "return Err(error!(PumpError::InvalidCreator));}t}};")],
    'n306_match': [(L306, "  let t=match new{Some(t)=>t,None=>return Err(error!(PumpError::CtoNewCreatorRequired))};")],
    'n306_iflet': [(L306, "  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};")],
    'n306_isnone': [(L306, "  if new.is_none(){return Err(error!(PumpError::CtoNewCreatorRequired));}let t=new.unwrap();")],
    'v307_rev': [(L307, "  if Pubkey::default()==t{return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}")],
    'v312_rev': [(L312, "  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};")],
    'v312_split': [(L312, "  if t==*holder_key{return Err(error!(PumpError::InvalidCreator));}if t==*sharing{return Err(error!(PumpError::InvalidCreator));}t};")],
    'v312_bitor': [(L312, "  if (t==*holder_key)|(t==*sharing){return Err(error!(PumpError::InvalidCreator));}t};")],
    'v326_match': [(L326, " match fee{Some(f)=>{if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}"),
                   (L338, L338 + "None=>{}}")],
    'v330_rev': [(L330, "  if st.cashback&&!holder{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}")],
    'v334_eq': [(L334, "  if st.fee_configurable==false{return Err(error!(PumpError::CreatorFeeNotConfigurable));}")],
    'v338_rev': [(L338, "  if f>st.max_fee||f==0{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}")],
    'v338_contains': [(L338, "  if !(1..=st.max_fee).contains(&f){return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}")],
    'v338_split': [(L338, "  if f==0{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}if f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}")],
    'v338_lt1': [(L338, "  if f<1||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}")],
    'v_mayhem_eq': [(" if st.mayhem{return", " if st.mayhem==true{return")],
    'validate_inline': [(VSIG, "#[inline] " + VSIG)],
    'validate_never': [(VSIG, "#[inline(never)] " + VSIG)],
    # ---------- wallet ----------
    'wallet_go': [(W0, " wallet(&ctx,collect_old)?;fn wallet(ctx:&Context<AdminCto>,go:bool)->Result<()>{if !go{return Ok(());}let a=&ctx.accounts;")],
    'wallet_deref': [(W0, W0.replace("let a=&ctx.accounts;", "let a=&*ctx.accounts;"))],
    'wallet_match': [(" if collect_old{wallet(&ctx)?;}", " if collect_old{match wallet(&ctx){Ok(())=>{},Err(e)=>return Err(e)}}")],
    'wallet_inline': [("fn wallet(ctx:", "#[inline] fn wallet(ctx:")],
    'wallet_early_ret': [(WEXE, 'if a.current_creator.executable{msg!("Creator is a program; fees left in the vaults");return Ok(());}if a.current_creator.owner!=&anchor_lang::system_program::ID{msg!("Creator is not a system-owned wallet; fees left in the vaults");}else{')],
    'w_writable_require': [(WWR, "require!(a.current_creator.is_writable,PumpError::CtoCreatorAccountNotWritable);")],
    'w_owner_deref': [("else if a.current_creator.owner!=&anchor_lang::system_program::ID{", "else if *a.current_creator.owner!=anchor_lang::system_program::ID{")],
    'w_native_rev': [(W557, "  let collection_native=anchor_spl::token::spl_token::native_mint::ID==a.quote_mint.key();")],
    'w_frozen_swap': [(W559 + "\n" + W560, W560 + "\n" + W559)],
    'w_source_frozen_if': [(W559, "  let source_frozen=if source_present{token_frozen(a.creator_vault_quote_token_account.as_ref())?}else{false};")],
    'w_coin_frozen_if': [(W560, "  let coin_frozen=if coin_present{token_frozen(a.coin_creator_vault_ata.as_ref())?}else{false};")],
    'w_ata_rev': [(W561, "  if coin_present||!collection_native{anchor_spl::associated_token::create_idempotent(")],
    'w_collect_match': [(W563, "    match crate::collect_v2::collect("), ("?{\n     let e=CollectCreatorFeeEvent{", "?{Some((collected,quote_mint))=>{\n     let e=CollectCreatorFeeEvent{"),
                        ("emit_cpi!(e);\n    }\n  }", "emit_cpi!(e);\n    }None=>{}}\n  }")],
    'w_clock_local': [("     let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,", "     let ts=Clock::get()?.unix_timestamp;let e=CollectCreatorFeeEvent{timestamp:ts,")],
    'w_frozen_match': [(WFZ, 'match token_frozen(a.current_creator_quote_token_account.as_ref())?{true=>{msg!("Creator quote token account is frozen; fees left in the vaults");}false=>{'),
                       (" }}Ok(())}\n let swept;", " }}}Ok(())}\n let swept;")],
    # ---------- sweep ----------
    'sweep_native_late': [(SW0 + NAT, SW0), ("  let old=a.current_creator.key();let bump=", "  " + NAT + "let old=a.current_creator.key();let bump=")],
    'sweep_gate_if': [(" swept=(shared&&holder).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);", " swept=if shared&&holder{sweep(&ctx,&holder_key)?}else{0};")],
    'sweep_gate_match': [(" swept=(shared&&holder).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);", " swept=match (shared,holder){(true,true)=>sweep(&ctx,&holder_key)?,_=>0};")],
    'sweep_gate_rev': [("swept=(shared&&holder).then(", "swept=(holder&&shared).then(")],
    'sweep_gate_unwrap_default': [(".transpose()?.unwrap_or(0);fn sweep", ".transpose()?.unwrap_or_default();fn sweep")],
    'sweep_deref': [(SW0, SW0.replace("let a=&ctx.accounts;", "let a=&*ctx.accounts;"))],
    'sweep_inline': [("fn sweep(ctx:", "#[inline] fn sweep(ctx:")],
    'sweep_dest_tuple': [(DEST, '  let (dest,_)=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID);')],
    'sweep_dest_ne_rev': [("if a.holder_creator_vault.key()!=dest{", "if dest!=a.holder_creator_vault.key(){")],
    'sweep_keys_eq': [(DESTCHK, "require_keys_eq!(a.holder_creator_vault.key(),dest,anchor_lang::error::ErrorCode::ConstraintSeeds);")],
    'sweep_coin_present': [(AMMF, "  let coin_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;"),
                           (L661, "  else if coin_present{crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(")],
    'sweep_amm_frozen_if': [(AMMF, "  let amm_frozen=if a.coin_creator_vault_ata.data_is_empty(){false}else{token_frozen(a.coin_creator_vault_ata.as_ref())?};")],
    'sweep_660_match': [(L660, "  if amm_frozen{require!(match token_raw_amount(a.coin_creator_vault_ata.as_ref()){Ok(v)=>v,Err(e)=>return Err(e)}==0,PumpError::CtoSharedVaultFrozen);}")],
    'bump_before_old': [(SEEDS, '  let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];')],
    'seeds_bump_inline': [(SEEDS, '  let old=a.current_creator.key();let bump=ctx.bumps.creator_vault;let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];')],
    'rent_inline': [(NARM, "  if native{let amount=a.creator_vault.lamports().saturating_sub(Rent::get()?.minimum_balance(0));")],
    'rent_named': [(NARM, "  if native{let rent=Rent::get()?;let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);")],
    'rent_ref': [(NARM, "  if native{let rent=&Rent::get()?;let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);")],
    'rent_lam_first': [(NARM, "  if native{let lam=a.creator_vault.lamports();let min=Rent::get()?.minimum_balance(0);let amount=lam.saturating_sub(min);")],
    'rent_max': [(NARM, "  if native{let min=Rent::get()?.minimum_balance(0);let lam=a.creator_vault.lamports();let amount=if lam>min{lam-min}else{0};")],
    'native_amount_ne': [("   if amount>0{crate::legacy_buy", "   if amount!=0{crate::legacy_buy")],
    'tok_amount_ne': [("else if amount>0{anchor_spl", "else if amount!=0{anchor_spl")],
    'tok_frozen_first': [("let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;",
                          "let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;")],
    'native_arm_ret': [("&[vaultseeds]).map(|()|amount)}else{Ok(amount)}}else{", "&[vaultseeds])?;return Ok(amount);}else{return Ok(amount);}}else{")],
    'native_q_ok': [("&[vaultseeds]).map(|()|amount)}else{Ok(amount)}}else{", "&[vaultseeds])?;Ok(amount)}else{Ok(amount)}}else{")],
    'tok_frozen_ok0': [("   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{", "   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);return Ok(0);}else if amount>0{")],
    # ---------- post-sweep ----------
    'seeds_inline': [(SEED2, ' let pb=[ctx.bumps.pool_authority];let signer_seeds:&[&[&[u8]]]=&[&[b"pool-authority",mint.as_ref(),&pb]];')],
    'seeds_bump_val': [(SEED2, ' let pb=ctx.bumps.pool_authority;let poolseeds:&[&[u8]]=&[b"pool-authority",mint.as_ref(),&[pb]];let signer_seeds:&[&[&[u8]]]=&[poolseeds];')],
    'su_iflet_match': [(SUIF, " match sharing_update{Some(val)=>{"), (" }\n let (old_creator", " }None=>{}}\n let (old_creator")],
    'su_ref': [(SUIF, " if let Some(val)=&sharing_update{"), (SUCPI_END, "program:a.pump_fees.to_account_info()},signer_seeds),*val)?;")],
    'su_with_signer': [("admin_cto_sharing_config(CpiContext::new_with_signer(", "admin_cto_sharing_config(CpiContext::new("),
                       (SUCPI_END, "program:a.pump_fees.to_account_info()}).with_signer(signer_seeds),val)?;")],
    'pool_with_signer': [("admin_cto_pool(CpiContext::new_with_signer(", "admin_cto_pool(CpiContext::new("),
                         ("program:a.pump_amm.to_account_info()},signer_seeds),target,holder,fee)?;", "program:a.pump_amm.to_account_info()}).with_signer(signer_seeds),target,holder,fee)?;")],
    'pool_empty_first': [(POOL, " let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;")],
    'pool_owner_deref': [(POOL, " let pool_updated=*a.pool.owner==AMM && !a.pool.data_is_empty();")],
    'pool_nested': [(POOL, " let pool_updated=if a.pool.owner==&AMM{!a.pool.data_is_empty()}else{false};")],
    'pool_match_cpi': [("},signer_seeds),target,holder,fee)?;", "},signer_seeds),target,holder,fee).map_err(|e|e)?;")],
    'holder_before_creator': [("  curve.creator=target;\n  curve.is_holder_reward=holder;\n", "  curve.is_holder_reward=holder;\n  curve.creator=target;\n")],
    'cashback_before_holder': [("  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;", "  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;")],
    'curve_deref': [("  let curve=&mut ctx.accounts.bonding_curve;", "  let curve=&mut *ctx.accounts.bonding_curve;")],
    'curve_flat': [(" let (old_creator,old_fee)={\n", " \n"), (" (old_creator,old_fee)};\n", " \n")],
    'a_reborrow_deref': [(" let a=&ctx.accounts;\n let pool_updated", " let a=&*ctx.accounts;\n let pool_updated")],
    'ev_new_creator_local': [("new_creator:a.bonding_curve.creator,", "new_creator:target,")],
    'ev_flags_local': [("is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,", "is_holder_reward:holder,is_cashback_coin:cashback,")],
    'ev_fee_local': [("new_creator_fee_bps:a.bonding_curve.creator_fee_bps,", "new_creator_fee_bps:fee.unwrap_or(old_fee),")],
    'ev_reset_shared': [("sharing_config_reset:sharing_update.is_some(),", "sharing_config_reset:shared,")],
    'ev_clock_first': [(" let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,", " let ts=Clock::get()?.unix_timestamp;let e=AdminCtoEvent{timestamp:ts,")],
    'ev_mint_reload': [("authority:a.admin_set_creator_authority.key(),mint,", "authority:a.admin_set_creator_authority.key(),mint:a.mint.key(),")],
    'pool_early': [(POOL, ""), (SEED2, " let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();" + SEED2)],
    'tf_inline': [("fn token_frozen(a:&AccountInfo)", "#[inline] fn token_frozen(a:&AccountInfo)")],
    'tra_inline': [("fn token_raw_amount(a:&AccountInfo)", "#[inline] fn token_raw_amount(a:&AccountInfo)")],
}
K4 = ['region2_tree', 'wallet_flags', 'fee_unwrap', 'canedit_first', 'old_fee_first']
# ---------- K5-compatible variants (base k4 + bump_before_old + su_iflet_match) ----------
R2 = "let (sharing_update,collect_old)=if shared{if holder{(Some(None),false)}else{target=st.creator;(Some(new),false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default())};"
SEEDS_B = '  let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];'
DOC = "  let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);"
DOCOIN = "  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;"
GENES.update({
    'su_match_ref': [(" match sharing_update{Some(val)=>{", " match &sharing_update{Some(val)=>{"), (SUCPI_END, "program:a.pump_fees.to_account_info()},signer_seeds),*val)?;")],
    'su_none_first': [(" match sharing_update{Some(val)=>{", " match sharing_update{None=>{}Some(val)=>{"), (" }None=>{}}\n let (old_creator", " }}\n let (old_creator")],
    'sweep_native_late_b': [(SW0 + NAT, SW0), ("  let bump=[ctx.bumps.creator_vault];let old=", "  " + NAT + "let bump=[ctx.bumps.creator_vault];let old=")],
    'seeds_bump_inline_b': [(SEEDS_B, '  let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];')],
    'r2_holder_flip': [(R2, "let (sharing_update,collect_old)=if shared{if !holder{target=st.creator;(Some(new),false)}else{(Some(None),false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default())};")],
    'r2_shared_flip': [(R2, "let (sharing_update,collect_old)=if !shared{(None,!st.holder_reward&&st.creator!=Pubkey::default())}else if holder{(Some(None),false)}else{target=st.creator;(Some(new),false)};")],
    'r2_match': [(R2, "let (sharing_update,collect_old)=match (shared,holder){(true,true)=>(Some(None),false),(true,false)=>{target=st.creator;(Some(new),false)}_=>(None,!st.holder_reward&&st.creator!=Pubkey::default())};")],
    'r2_co_rev': [(R2, R2.replace("(None,!st.holder_reward&&st.creator!=Pubkey::default())", "(None,st.creator!=Pubkey::default()&&!st.holder_reward)"))],
    'r2_su_inner': [(R2, "let (sharing_update,collect_old)=if shared{(Some(if holder{None}else{target=st.creator;new}),false)}else{(None,!st.holder_reward&&st.creator!=Pubkey::default())};")],
    'doc_if': [(DOC, "  let do_collect=if collection_native{true}else{!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?};")],
    'doc_rev': [(DOC, "  let do_collect=(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?)||collection_native;")],
    'docoin_if': [(DOCOIN, "  let do_coin=if coin_present{!token_frozen(a.coin_creator_vault_ata.as_ref())?}else{false};")],
    'docoin_inline_present': [("  let coin_present=!a.coin_creator_vault_ata.data_is_empty();\n" + DOC + "\n" + DOCOIN,
                               "  let coin_present=!a.coin_creator_vault_ata.data_is_empty();\n" + DOC + "\n" + DOCOIN.replace("coin_present&&", "!a.coin_creator_vault_ata.data_is_empty()&&"))],
    'wflags_order': [("\n" + DOC + "\n" + DOCOIN, "\n" + DOCOIN + "\n" + DOC)],
})
# ---------- sweep gate as a phi of constants coalesced with collect_old (residual catalog) ----------
BLK5 = "let (holder,cashback,target,sharing_update,collect_old)={"
BLKC5 = "(holder,cashback,target,sharing_update,collect_old)};let mut target=target;"
GATE = " swept=(shared&&holder).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);"
GENES.update({
    'r2_sweep3': [(BLK5, "let (holder,cashback,target,sharing_update,collect_old,go)={"),
                  (R2, "let (sharing_update,collect_old,go)=if shared{if holder{(Some(None),false,true)}else{target=st.creator;(Some(new),false,false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),false)};"),
                  (BLKC5, "(holder,cashback,target,sharing_update,collect_old,go)};let mut target=target;"),
                  (GATE, " swept=go.then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);")],
    'r2_skip3': [(BLK5, "let (holder,cashback,target,sharing_update,collect_old,skip)={"),
                 (R2, "let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(new),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};"),
                 (BLKC5, "(holder,cashback,target,sharing_update,collect_old,skip)};let mut target=target;"),
                 (GATE, " swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);")],
    'r2_skip3_if': [(BLK5, "let (holder,cashback,target,sharing_update,collect_old,skip)={"),
                    (R2, "let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(new),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};"),
                    (BLKC5, "(holder,cashback,target,sharing_update,collect_old,skip)};let mut target=target;"),
                    (GATE, " swept=if skip{0}else{sweep(&ctx,&holder_key)?};")],
    'r2_sweep3_if': [(BLK5, "let (holder,cashback,target,sharing_update,collect_old,go)={"),
                     (R2, "let (sharing_update,collect_old,go)=if shared{if holder{(Some(None),false,true)}else{target=st.creator;(Some(new),false,false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),false)};"),
                     (BLKC5, "(holder,cashback,target,sharing_update,collect_old,go)};let mut target=target;"),
                     (GATE, " swept=if go{sweep(&ctx,&holder_key)?}else{0};")],
})
# ---------- tuple element order of the state block (MIR local order -> alloca order) ----------
def _tup(order):
    o = ','.join(order)
    return [(BLK5, "let (" + o + ")={"), (BLKC5, "(" + o + ")};let mut target=target;")]
GENES.update({
    'tup_target_first': _tup(['target', 'holder', 'cashback', 'sharing_update', 'collect_old']),
    'tup_su_first': _tup(['sharing_update', 'holder', 'cashback', 'target', 'collect_old']),
    'tup_rev': _tup(['collect_old', 'sharing_update', 'target', 'cashback', 'holder']),
    'tup_target_last': _tup(['holder', 'cashback', 'sharing_update', 'collect_old', 'target']),
    'tup_co_first': _tup(['collect_old', 'holder', 'cashback', 'target', 'sharing_update']),
    'tup_ts_first': _tup(['target', 'sharing_update', 'holder', 'cashback', 'collect_old']),
})
# ---------- outlined (cold) error constructors keep to_string out of execute (residual: 307/312 outlined in orig) ----------
GENES.update({
    'cold312': [(L312, "  if t==*holder_key||t==*sharing{#[cold]#[inline(never)]fn e312()->Error{error!(PumpError::InvalidCreator)}return Err(e312());}t};")],
    'cold307': [(L307, "  if t==Pubkey::default(){#[cold]#[inline(never)]fn e307(t:Pubkey)->Error{error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default()))}return Err(e307(t));}")],
    'cold312_inl': [(L312, "  if t==*holder_key||t==*sharing{#[cold]fn e312()->Error{error!(PumpError::InvalidCreator)}return Err(e312());}t};")],
    'cold307_inl': [(L307, "  if t==Pubkey::default(){#[cold]fn e307(t:Pubkey)->Error{error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default()))}return Err(e307(t));}")],
})
