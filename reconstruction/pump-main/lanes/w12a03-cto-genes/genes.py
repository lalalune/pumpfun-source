# Gene catalog for 0x22a10 admin_cto::execute, ported onto main 20a1ae9c0 (= #2642 source).
#
# Every gene is a list of exact (old, new) substitutions over programs/pump/src/creator/admin_cto.rs as
# it stands on main. Each substitution keeps the newline count, so every require!/error! site keeps its
# line (line numbers are instruction immediates). `apply(text, names)` applies genes in order and fails
# if an old string does not occur exactly once.
#
# SRC names the lane/branch the mechanism came from. Genes marked "revert" undo a mechanism main already
# carries (measured so the table shows what each landed piece is worth on today's source).
SHARED = "let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();"
QL = "let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);"
HK = "let (holder_key,_)=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);"
ST = ("let st=CtoState{creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,"
      "holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled,"
      "fee_configurable:a.global.creator_fee_configurable};")
HOLDER = "let holder=holder==Some(true);"
CB = "let cashback=!holder&&st.cashback;"
VAL = "let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;"
SU = "let sharing_update=if shared{Some(if holder{None}else{new})}else{None};"
CO = "let collect_old=!shared&&!st.holder_reward&&st.creator!=Pubkey::default();"
TO = "if shared&&!holder{target=st.creator;}"
TUP = "(holder,cashback,target,sharing_update,collect_old)};"
OPEN = "let (holder,cashback,target,sharing_update,collect_old)={"
PREP = "crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;"
REQ410 = " require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);"
GATE = " swept=(shared&&holder).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);"
SWEEPSIG = "fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;"
NATIVE = "let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;"
SEEDS = "let old=a.current_creator.key();let bump=[ctx.bumps.creator_vault];let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&bump];"
RENT = "let min=Rent::get()?.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);"
NATARM = ("crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&[vaultseeds]).map(|()|amount)}else{Ok(amount)}}else{")
TOKRD = "let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;"
CREATE_H = ("anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{"
            "payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.holder_creator_vault_quote_token_account.to_account_info(),"
            "authority:a.holder_creator_vault.to_account_info(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),"
            "token_program:a.quote_token_program.to_account_info()}))")
TVT = ("crate::collect_v2::transfer_vault_tokens(&a.quote_token_program,&a.creator_vault_quote_token_account,&a.holder_creator_vault_quote_token_account,"
       "&a.creator_vault,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&[vaultseeds])")
TOK719 = "   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{" + CREATE_H + "?;" + TVT + "?;}\n   Ok(amount)}\n"
POOLSEEDS = " let pb=[ctx.bumps.pool_authority];let poolseeds:&[&[u8]]=&[b\"pool-authority\",mint.as_ref(),&pb];let signer_seeds:&[&[&[u8]]]=&[poolseeds];"
TCF_OLD = ("TransferCreatorFeesToPumpV2{system_program:a.system_program.to_account_info(),quote_mint:a.quote_mint.to_account_info(),"
           "token_program:a.quote_token_program.to_account_info(),payer:a.admin_set_creator_authority.to_account_info(),")
TCF_NEW = ("TransferCreatorFeesToPumpV2{payer:a.admin_set_creator_authority.to_account_info(),quote_mint:a.quote_mint.to_account_info(),"
           "token_program:a.quote_token_program.to_account_info(),system_program:a.system_program.to_account_info(),")
W_HEAD = " if collect_old{wallet(&ctx)?;}fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;"
W_EXEC = "if a.current_creator.executable{msg!(\"Creator is a program; fees left in the vaults\");}else if"
EV = " let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,"

G = {}
SRC = {}


def gene(name, src, edits):
    assert name not in G, name
    G[name] = edits
    SRC[name] = src


# ---------------- execute prologue ----------------
gene('ql_before_shared', 'w10r1-admincto-hillclimb r1 / w9r2 edits.py', [(SHARED + QL, QL + SHARED)])
gene('hk_after_shared', 'w10r1-admincto-hillclimb genes1', [(HK + SHARED, SHARED + HK)])
gene('hk_after_ql', 'w10r1-admincto-hillclimb genes1', [(HK + SHARED + QL, SHARED + QL + HK)])
gene('mint_inline_hk', 'w10r1-admincto-hillclimb genes1', [("let mint=a.mint.key();" + HK, HK.replace('mint.as_ref()', 'a.mint.key().as_ref()') + "let mint=a.mint.key();")])
gene('hk_dot0', 'w10r1-admincto-hillclimb genes2 / y1-cto-callee g13', [(HK, "let holder_key=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID).0;")])
gene('mint_ctx', 'w10r1-admincto-hillclimb genes2', [(" let a=&ctx.accounts;let mint=a.mint.key();", " let mint=ctx.accounts.mint.key();let a=&ctx.accounts;")])
gene('a_deref', 'w10r1-admincto-hillclimb genes1', [(" let a=&ctx.accounts;let mint=a.mint.key();", " let a=&*ctx.accounts;let mint=a.mint.key();")])
gene('shared_owner_first', 'w10r1-admincto-hillclimb genes1', [(SHARED, "let shared=a.sharing_config.owner==&FEES&&a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty();")])
gene('shared_empty_first', 'w10r1-admincto-hillclimb genes1', [(SHARED, "let shared=!a.sharing_config.data_is_empty()&&a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES;")])
gene('shared_key_lhs', 'w10r1-admincto-hillclimb genes1 / y1-cto-diffwin', [(SHARED, "let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();")])
gene('shared_bitand', 'w10r1-admincto-hillclimb genes1', [(SHARED, "let shared=(a.bonding_curve.creator==a.sharing_config.key())&(a.sharing_config.owner==&FEES)&!a.sharing_config.data_is_empty();")])
gene('shared_owner_deref', 'w10r1-admincto-hillclimb genes2', [(SHARED, SHARED.replace("a.sharing_config.owner==&FEES", "*a.sharing_config.owner==FEES"))])
gene('ql_inline_ctostate', 'w10r1-admincto-hillclimb genes1 / w10r1-admincto-region1of6', [(QL, ""), ("quote_locked,holder_enabled", "quote_locked:crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global),holder_enabled")])
gene('ctostate_r1order', 'w10r1-admincto-region1of6 (literal order, quote_locked inline)', [(QL, ""), (ST,
     "let st=CtoState{mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,"
     "quote_locked:crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global),creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,"
     "holder_enabled:a.global.is_holder_reward_enabled,fee_configurable:a.global.creator_fee_configurable};")])
gene('ctostate_gfirst', 'x2-cto-cashback-and1-plus-120b knob gfirst', [(ST,
     "let st=CtoState{max_fee:a.global.max_configurable_creator_fee_bps,holder_enabled:a.global.is_holder_reward_enabled,fee_configurable:a.global.creator_fee_configurable,"
     "creator:a.bonding_curve.creator,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked};")])
gene('gq_clone', 'w10r1-admincto-hillclimb genes2', [(QL, QL.replace("a.bonding_curve.quote_mint,", "a.bonding_curve.quote_mint.clone(),"))])

# ---------------- holder / cashback ----------------
gene('holder_unwrap_or', 'w10r1-admincto-hillclimb genes1', [(HOLDER, "let holder=holder.unwrap_or(false);")])
gene('holder_unwrap_r1', 'w10r1-admincto-region1of6 / w9r2 edits.py holder_unwrap', [(HOLDER + CB, "let holder=holder.unwrap_or(false);let cashback=!holder&st.cashback;")])
gene('holder_matches', 'w10r1-admincto-hillclimb genes1', [(HOLDER, "let holder=matches!(holder,Some(true));")])
gene('holder_is_some_and', 'w10r1-admincto-hillclimb genes1', [(HOLDER, "let holder=holder.is_some_and(|h|h);")])
gene('holder_unwrap_default', 'w10r1-admincto-hillclimb genes3', [(HOLDER, "let holder=holder.unwrap_or_default();")])
gene('holder_iflet', 'w10r1-admincto-hillclimb genes3', [(HOLDER, "let holder=if let Some(h)=holder{h}else{false};")])
gene('holder_match', 'w10r1-admincto-hillclimb genes3', [(HOLDER, "let holder=match holder{Some(h)=>h,None=>false};")])
gene('holder_before_st', 'w10r1-admincto-hillclimb genes1', [(" " + HOLDER, ""), (OPEN, HOLDER + OPEN)])
gene('cashback_after_validate', 'w10r1-admincto-hillclimb genes1', [(CB + VAL, VAL + CB)])
gene('cashback_bitand', 'w10r1-admincto-hillclimb genes1', [(CB, "let cashback=!holder&st.cashback;")])
gene('cashback_end', 'w10r1-admincto-hillclimb genes1', [(CB, ""), (TO + "(holder", TO + CB + "(holder")])
gene('cashback_late', 'x1-cto-cashback-after-validate-holder-and1 / w9r2 edits.py', [(CB, ""), (TUP, "(holder,st.cashback,target,sharing_update,collect_old)};"),
     ("  curve.is_cashback_coin=cashback;", "  curve.is_cashback_coin=!holder&&cashback;")])

# ---------------- validate ----------------
gene('st_by_value', 'w10r1-admincto-hillclimb genes1 / y1-cto-callee d', [("struct CtoState{", "#[derive(Clone,Copy)]struct CtoState{"), ("fn validate(st:&CtoState,", "fn validate(st:CtoState,"), ("validate(&st,", "validate(st,")])
gene('keys_byval', 'y1-cto-diffwin / w10r1-admincto-region2of6 cp3', [("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{", "holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{"),
     ("*holder_key}else{", "holder_key}else{"), ("if t==*holder_key||t==*sharing{", "if t==holder_key||t==sharing{"),
     ("new,&holder_key,&a.sharing_config.key())?", "new,holder_key,a.sharing_config.key())?")])
gene('hk_byval', 'y1-cto-callee (holder_key by value, sharing by ref)', [("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{", "holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>{"),
     ("*holder_key}else{", "holder_key}else{"), ("if t==*holder_key||t==*sharing{", "if t==holder_key||t==*sharing{"),
     ("new,&holder_key,&a.sharing_config.key())?", "new,holder_key,&a.sharing_config.key())?")])
gene('sharing_byval', 'w10r1-admincto-hillclimb validate_sharing_ref (inverse)', [("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{", "holder_key:&Pubkey,sharing:Pubkey)->Result<Pubkey>{"),
     ("if t==*holder_key||t==*sharing{", "if t==*holder_key||t==sharing{"), ("new,&holder_key,&a.sharing_config.key())?", "new,&holder_key,a.sharing_config.key())?")])
gene('sharing_key_field', 'w10r1-admincto-hillclimb genes3 sharing_key_once / y1-cto-callee b4', [("new,&holder_key,&a.sharing_config.key())?", "new,&holder_key,a.sharing_config.key)?")])
gene('arg_swap', 'w10r1-admincto-region1of6 / x1-cto-validate-sharing-arg-first', [("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{", "sharing:&Pubkey,holder_key:&Pubkey)->Result<Pubkey>{"),
     ("new,&holder_key,&a.sharing_config.key())?", "new,&a.sharing_config.key(),&holder_key)?")])
gene('or_order', 'w10r1-admincto-hillclimb genes1', [("if t==*holder_key||t==*sharing{", "if t==*sharing||t==*holder_key{")])
gene('zero_eq_rev', 'w10r1-admincto-hillclimb genes1', [("if t==Pubkey::default(){", "if Pubkey::default()==t{")])
gene('fee_range_rev', 'w10r1-admincto-hillclimb genes1', [("if f==0||f>st.max_fee{", "if f>st.max_fee||f==0{")])
gene('fee_range_contains', 'w10r1-admincto-hillclimb genes1', [("if f==0||f>st.max_fee{", "if !(1..=st.max_fee).contains(&f){")])
gene('cashback_check_rev', 'w10r1-admincto-hillclimb genes1', [("if !holder&&st.cashback{", "if st.cashback&&!holder{")])
gene('mayhem_eq_true', 'w10r1-admincto-hillclimb genes1', [(" if st.mayhem{return", " if st.mayhem==true{return")])
gene('hr_check_rev', 'w10r1-admincto-hillclimb genes1', [("if st.holder_reward&&!holder{", "if !holder&&st.holder_reward{")])
gene('hr_nested_take', 'y1-cto-callee v3 (#2370 + #2416 rebuild)', [("new:Option<Pubkey>,holder_key:&Pubkey", "mut new:Option<Pubkey>,holder_key:&Pubkey"),
     (" if holder&&!st.holder_reward&&!st.holder_enabled{", " let target=if holder{if !st.holder_reward&&!st.holder_enabled{"),
     (" let target=if holder{if new.is_some(){", "  if new.take().is_some(){"), ("  let Some(t)=new else{", "  let Some(t)=new.take() else{")])
gene('hr_nested', 'y1-cto-callee v3 without take()', [(" if holder&&!st.holder_reward&&!st.holder_enabled{", " let target=if holder{if !st.holder_reward&&!st.holder_enabled{"),
     (" let target=if holder{if new.is_some(){", "  if new.is_some(){")])
gene('new_take', 'y1-cto-callee v3 take() only', [("new:Option<Pubkey>,holder_key:&Pubkey", "mut new:Option<Pubkey>,holder_key:&Pubkey"),
     ("if new.is_some(){", "if new.take().is_some(){"), ("  let Some(t)=new else{", "  let Some(t)=new.take() else{")])
gene('n306_match', 'w10r1-admincto-hillclimb genes3', [("  let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};", "  let t=match new{Some(t)=>t,None=>return Err(error!(PumpError::CtoNewCreatorRequired))};")])
gene('n306_okorelse', 'w10r1-admincto-hillclimb genes3 / y1-cto-callee v2', [("  let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};", "  let t=new.ok_or_else(||error!(PumpError::CtoNewCreatorRequired))?;")])
gene('n306_iflet', 'w10r1-admincto-hillclimb genes3', [("  let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};", "  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};")])
gene('n306_isnone', 'w10r1-admincto-hillclimb genes3', [("  let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};", "  if new.is_none(){return Err(error!(PumpError::CtoNewCreatorRequired));}let t=new.unwrap();")])
gene('n298_iflet', 'w10r1-admincto-hillclimb genes3', [("if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}", "if let Some(_)=new{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}")])
gene('n298_notnone', 'w10r1-admincto-hillclimb genes3 / y1-cto-blocks v-none-check', [("if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}", "if !new.is_none(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}")])
gene('feematch', 'w10r1-admincto-region2of6 feematch', [(" if let Some(f)=fee{if st.quote_locked{", " match fee{None=>{},Some(f)=>{if st.quote_locked{"),
     ("return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}", "return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}}")])
gene('validate_inline', 'w10r1-admincto-hillclimb genes2', [("fn validate(st:", "#[inline] fn validate(st:")])
gene('errseq_target', 'w10r1-admincto-errseq #2564 / w9r2 edits.py (validate returns st.creator when shared, shared last arg)', [
     ("sharing:&Pubkey)->Result<Pubkey>{", "sharing:&Pubkey,shared:bool)->Result<Pubkey>{"),
     (VAL, "let target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key(),shared)?;"), (TO, ""),
     ("  if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}t};", "  if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};")])
gene('errseq_target2', 'w10r1-admincto-hillclimb genes3 validate_shared_arm2 (shared second arg)', [
     ("fn validate(st:&CtoState,holder:bool,", "fn validate(st:&CtoState,shared:bool,holder:bool,"),
     (VAL, "let target=validate(&st,shared,holder,fee,new,&holder_key,&a.sharing_config.key())?;"), (TO, ""),
     ("  if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}t};", "  if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};")])

# ---------------- sharing_update / collect_old / target ----------------
gene('su_match', 'w10r1-admincto-hillclimb genes1', [(SU, "let sharing_update=match (shared,holder){(true,true)=>Some(None),(true,false)=>Some(new),_=>None};")])
gene('su_then', 'w10r1-admincto-hillclimb genes1', [(SU, "let sharing_update=shared.then(||if holder{None}else{new});")])
gene('su_holder_first', 'w10r1-admincto-hillclimb genes2', [(SU, "let sharing_update=if !shared{None}else if holder{Some(None)}else{Some(new)};")])
gene('co_reorder', 'w10r1-admincto-hillclimb genes1', [(CO, "let collect_old=st.creator!=Pubkey::default()&&!st.holder_reward&&!shared;")])
gene('co_su_isnone', 'revert of #2642 collect_old !shared', [(CO, "let collect_old=sharing_update.is_none()&&!st.holder_reward&&st.creator!=Pubkey::default();")])
gene('to_before_su', 'w10r1-admincto-hillclimb genes1', [(SU + CO + TO, TO + SU + CO)])
gene('to_ifexpr', 'y1-cto-diffwin target as if-expr / hillclimb to_ifexpr2', [(VAL, VAL.replace("let mut target", "let target")), (TO, "let target=if shared&&!holder{st.creator}else{target};")])
gene('region2_tree', 'w10r1-admincto-region2of6 #2515 / w9r2 edits.py region2_tree', [(SU + CO + TO,
     "let (sharing_update,collect_old)=if shared{if holder{(Some(None),false)}else{target=st.creator;(Some(new),false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default())};")])
gene('skip_tree', 'w10r1-admincto-region2of6 mutations.py tree (phi-of-constants skip gates the sweep)', [(SU + CO + TO + TUP,
     "let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(new),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};"),
     (OPEN, "let (holder,cashback,target,sharing_update,collect_old,skip)={"), (GATE, " swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);")])
gene('skip_tree_if', 'w10r1-admincto-region2of6 cp3 (skip gate as if/else)', [(SU + CO + TO + TUP,
     "let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(new),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};"),
     (OPEN, "let (holder,cashback,target,sharing_update,collect_old,skip)={"), (GATE, " swept=if !skip{sweep(&ctx,&holder_key)?}else{0};")])
gene('prep_after_410', 'w10r1-admincto-hillclimb genes1', [(" " + PREP, ""), (REQ410, REQ410 + PREP)])

# ---------------- wallet (collect old creator) ----------------
gene('wallet_flags', 'w10r1-admincto-region6of6 #2518 / y1-cto-diffwin / w9r2 edits.py', [
     ("let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();\n  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;\n  let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;",
      "\n  let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);\n  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;"),
     ("\n  if collection_native||(source_present&&!source_frozen){", "\n  if do_collect{"), ("\n  if coin_present&&!coin_frozen{", "\n  if do_coin{")])
gene('wallet_go_param', 'w10r1-admincto-hillclimb genes1 wallet_flag', [(W_HEAD, " wallet(&ctx,collect_old)?;fn wallet(ctx:&Context<AdminCto>,go:bool)->Result<()>{if !go{return Ok(());}let a=&ctx.accounts;")])
gene('wallet_deref', 'w10r1-admincto-hillclimb genes1', [(W_HEAD, W_HEAD.replace("let a=&ctx.accounts;", "let a=&*ctx.accounts;"))])
gene('wallet_early_returns', 'w10r1-admincto-hillclimb genes2', [(W_EXEC, "if a.current_creator.executable{msg!(\"Creator is a program; fees left in the vaults\");return Ok(());}if")])
gene('wallet_inline', 'w10r1-admincto-hillclimb genes2', [("fn wallet(ctx:", "#[inline] fn wallet(ctx:")])
gene('wallet_call_expr', 'w10r1-admincto-hillclimb genes2', [(" if collect_old{wallet(&ctx)?;}", " if collect_old{wallet(&ctx)?}")])
gene('coin_frozen_if', 'w10r1-admincto-hillclimb genes2', [("  let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;", "  let coin_frozen=if coin_present{token_frozen(a.coin_creator_vault_ata.as_ref())?}else{false};")])
gene('source_frozen_if', 'w10r1-admincto-hillclimb genes2', [("  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;", "  let source_frozen=if source_present{token_frozen(a.creator_vault_quote_token_account.as_ref())?}else{false};")])

# ---------------- sweep ----------------
gene('frozen_first', 'y1-cto-blocks / y1-cto-spill / w10r1-admincto-hillclimb sweep_frozen_first', [(TOKRD, "let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;")])
gene('native_late', 'y1-cto-diffwin sweep native late / hillclimb sweep_native_late', [(SWEEPSIG + NATIVE, SWEEPSIG), ("  " + SEEDS, "  " + NATIVE + SEEDS)])
gene('bump_before_old', 'revert of #2642 old-before-bump', [(SEEDS, "let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&bump];")])
gene('native_keep', 'revert of #2642 native passthrough', [(NATARM, "crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&[vaultseeds])?;}Ok(amount)}else{")])
gene('gate_ifexpr', 'revert of #2642 transpose gate (if-expr form)', [(GATE, " swept=if shared&&holder{sweep(&ctx,&holder_key)?}else{0};")])
gene('gate_rev', 'w10r1-admincto-hillclimb sweep_gate_rev / y1-cto-diffwin', [(GATE, GATE.replace("(shared&&holder)", "(holder&&shared)"))])
gene('gate_inside', 'w10r1-admincto-hillclimb sweep_gate_inside', [(GATE + SWEEPSIG, " swept=sweep(&ctx,&holder_key,shared&&holder)?;fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey,go:bool)->Result<u64>{if !go{return Ok(0);}let a=&ctx.accounts;")])
gene('sweep_hk_val', 'w10r1-admincto-hillclimb genes1 / y1-cto-callee g11', [("then(||sweep(&ctx,&holder_key))", "then(||sweep(&ctx,holder_key))"), ("fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)", "fn sweep(ctx:&Context<AdminCto>,holder_key:Pubkey)")])
gene('sweep_deref', 'w10r1-admincto-hillclimb genes1', [(SWEEPSIG, SWEEPSIG.replace("let a=&ctx.accounts;", "let a=&*ctx.accounts;"))])
gene('sweep_inline', 'w10r1-admincto-hillclimb genes2', [("fn sweep(ctx:", "#[inline] fn sweep(ctx:")])
gene('sweep_coin_present', 'w10r1-admincto-hillclimb genes1', [("let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(", "let coin_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=coin_present&&token_frozen("),
     ("else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm", "else if coin_present{crate::pump_amm")])
gene('amm_frozen_if', 'w10r1-admincto-hillclimb genes2', [("let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(a.coin_creator_vault_ata.as_ref())?;", "let amm_frozen=if a.coin_creator_vault_ata.data_is_empty(){false}else{token_frozen(a.coin_creator_vault_ata.as_ref())?};")])
gene('dest_ne_rev', 'w10r1-admincto-hillclimb genes1', [("if a.holder_creator_vault.key()!=dest{", "if dest!=a.holder_creator_vault.key(){")])
gene('dest_tuple', 'w10r1-admincto-hillclimb genes2', [("let dest=Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID).0;", "let (dest,_)=Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID);")])
gene('require_keys_eq_648', 'w10r1-admincto-hillclimb genes2', [("if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}", "require_keys_eq!(a.holder_creator_vault.key(),dest,anchor_lang::error::ErrorCode::ConstraintSeeds);")])
gene('native_key_eq_ref', 'w10r1-admincto-hillclimb genes2', [(SWEEPSIG + NATIVE, SWEEPSIG + "let native=*a.quote_mint.to_account_info().key==anchor_spl::token::spl_token::native_mint::ID;")])
gene('seeds_before_amm', 'w10r1-admincto-hillclimb genes2', [("  " + SEEDS, "  "), ("  let amm_frozen=", "  " + SEEDS + "let amm_frozen=")])
gene('tcf_field_order', 'y1-cto-diffwin TransferCreatorFeesToPumpV2 field order', [(TCF_OLD, TCF_NEW)])
gene('amount_gt0_ne', 'w10r1-admincto-hillclimb genes1', [("   if amount>0{crate::legacy_buy", "   if amount!=0{crate::legacy_buy")])
gene('tok_amount_ne', 'w10r1-admincto-hillclimb genes1', [("else if amount>0{anchor_spl", "else if amount!=0{anchor_spl")])
gene('rent_inline', 'w10r1-admincto-hillclimb genes2', [(RENT, "let amount=a.creator_vault.lamports().saturating_sub(Rent::get()?.minimum_balance(0));")])
gene('rent_checked_sub', 'w10r1-admincto-hillclimb genes2', [(RENT, "let min=Rent::get()?.minimum_balance(0);let amount=a.creator_vault.lamports().checked_sub(min).unwrap_or(0);")])
gene('rent_max', 'w10r1-admincto-hillclimb genes2', [(RENT, "let min=Rent::get()?.minimum_balance(0);let lam=a.creator_vault.lamports();let amount=if lam>min{lam-min}else{0};")])
gene('rent_local', 'x2-cto-rent-local-24b-frame (named Rent local live across the CPIs)', [(RENT, "let rent=Rent::get()?;let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);")])
gene('rent_ref_local', 'x2-cto-rent-local-24b-frame rent-ref-temp-extension', [(RENT, "let rent=&Rent::get()?;let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);")])
gene('rent_local_inline_min', 'x2-cto-rent-local-24b-frame inline-min', [(RENT, "let rent=Rent::get()?;let amount=a.creator_vault.lamports().saturating_sub(rent.minimum_balance(0));")])
gene('rent_block', 'x2-cto-rent-local-24b-frame block-scoped control', [(RENT, "let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);")])
gene('rent_after_lamports', 'x2-cto-rent-local-24b-frame after-lamports-read', [(RENT, "let lamports=a.creator_vault.lamports();let rent=Rent::get()?;let amount=lamports.saturating_sub(rent.minimum_balance(0));")])
gene('rent_option_hoisted', 'x2-cto-rent-local-24b-frame option-hoisted-before-vault-seeds', [("  " + SEEDS, "  let rent=if native{Some(Rent::get()?)}else{None};" + SEEDS),
     ("  if native{" + RENT, "  if let Some(rent)=rent{let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);")])
gene('tok_andthen', 'x2-cto-sweepg tokenandthen (token CPIs chained into one passthrough Result)', [(TOK719,
     "   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);Ok(amount)}else if amount>0{" + CREATE_H + ".and_then(|()|" + TVT + ").map(|()|amount)}else{Ok(amount)}\n   }\n")])
gene('tok_andthen_0', 'x2-cto-sweepg tokenandthen + frozen/else arms Ok(0)', [(TOK719,
     "   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);Ok(0)}else if amount>0{" + CREATE_H + ".and_then(|()|" + TVT + ").map(|()|amount)}else{Ok(0)}\n   }\n")])
gene('tok_map', 'x2-cto-sweepg token arm map passthrough', [(TOK719,
     "   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);Ok(amount)}else if amount>0{" + CREATE_H + "?;" + TVT + ".map(|()|amount)}else{Ok(amount)}\n   }\n")])
gene('tok_frozen0', 'x2-cto-sweepg frozen arm Ok(0) (token CPIs keep ?)', [(TOK719,
     "   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);Ok(0)}else{if amount>0{" + CREATE_H + "?;" + TVT + "?;}Ok(amount)}\n   }\n")])
gene('vsigner', 'w10r1-admincto-region2of6 mutations.py vsigner', [("&[b\"creator-vault\",old.as_ref(),&bump];", "&[b\"creator-vault\",old.as_ref(),&bump];let vsigner:&[&[&[u8]];1]=&[vaultseeds];"),
     ("amount,&[vaultseeds]).map(|()|amount)}", "amount,vsigner).map(|()|amount)}"), ("amount,&[vaultseeds])?;}\n   Ok(amount)}", "amount,vsigner)?;}\n   Ok(amount)}")])
gene('tf_inline', 'w10r1-admincto-hillclimb genes2', [("fn token_frozen(a:&AccountInfo)", "#[inline] fn token_frozen(a:&AccountInfo)")])
gene('tra_inline', 'w10r1-admincto-hillclimb genes2', [("fn token_raw_amount(a:&AccountInfo)", "#[inline] fn token_raw_amount(a:&AccountInfo)")])

# ---------------- post-sweep: CPIs, curve store, event ----------------
gene('with_signer', 'w10r1-admincto-cpi r2 / x2 sws knob (with_signer only on the sharing CPI)', [("admin_cto_sharing_config(CpiContext::new_with_signer(", "admin_cto_sharing_config(CpiContext::new("),
     ("program:a.pump_fees.to_account_info()},signer_seeds),val)?;", "program:a.pump_fees.to_account_info()}).with_signer(signer_seeds),val)?;")])
gene('pool_with_signer', 'x2-cto-cashback-and1-plus-120b knob pws', [("admin_cto_pool(CpiContext::new_with_signer(", "admin_cto_pool(CpiContext::new("),
     ("program:a.pump_amm.to_account_info()},signer_seeds),target,holder,fee)?;", "program:a.pump_amm.to_account_info()}).with_signer(signer_seeds),target,holder,fee)?;")])
gene('poolseeds_inline', 'y1-cto-diffwin / w10r1-admincto-hillclimb seeds_after_su', [(POOLSEEDS, " let pb=[ctx.bumps.pool_authority];let signer_seeds:&[&[&[u8]]]=&[&[b\"pool-authority\",mint.as_ref(),&pb]];")])
gene('su_iflet_match', 'w10r1-admincto-hillclimb genes1', [(" if let Some(val)=sharing_update{", " match sharing_update{Some(val)=>{"), (" }\n let (old_creator", " }None=>{}}\n let (old_creator")])
gene('pool_empty_first', 'w10r1-admincto-state / hillclimb pool_order', [(" let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", " let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;")])
gene('pool_key_eq', 'w10r1-admincto-hillclimb genes1', [(" let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", " let pool_updated=*a.pool.owner==AMM && !a.pool.data_is_empty();")])
gene('pool_updated_early', 'w10r1-admincto-hillclimb genes2', [(POOLSEEDS, " let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();" + POOLSEEDS),
     (" let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();\n if pool_updated{", "\n if pool_updated{")])
gene('pool_neg_first', 'w10r1-admincto-hillclimb genes2', [(" if pool_updated{", " if !pool_updated{msg!(\"No canonical pump pool for this mint; curve only\");}else{"), (" }else{msg!(\"No canonical pump pool for this mint; curve only\");}", " }")])
gene('fee_unwrap', 'w10r1-admincto-state #2622 / w9r2 edits.py', [("  if let Some(f)=fee{curve.creator_fee_bps=f;}", "  curve.creator_fee_bps=fee.unwrap_or(old_fee);")])
gene('canedit_first', 'w10r1-admincto-state / hillclimb curve_edit_first / w9r2 edits.py', [("let old_fee=curve.creator_fee_bps;\n  curve.creator=target;", "let old_fee=curve.creator_fee_bps;curve.can_edit_creator_fee=false;\n  curve.creator=target;"),
     ("  curve.can_edit_creator_fee=false;\n (old_creator", "\n (old_creator")])
gene('old_fee_first', 'y1-cto-spill / w9r2 edits.py', [("let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;", "let old_fee=curve.creator_fee_bps;let old_creator=curve.creator;")])
gene('holder_before_creator', 'w10r1-admincto-hillclimb curve_swap_754_755', [("  curve.creator=target;\n  curve.is_holder_reward=holder;", "  curve.is_holder_reward=holder;\n  curve.creator=target;")])
gene('holder_after_cashback', 'y1-cto-blocks / y1-cto-diffwin / hillclimb curve_swap_755_756', [("  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;", "  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;")])
gene('curve_deref', 'w10r1-admincto-hillclimb genes2', [("  let curve=&mut ctx.accounts.bonding_curve;", "  let curve=&mut *ctx.accounts.bonding_curve;")])
gene('a_reborrow_drop', 'w10r1-admincto-hillclimb genes1', [(" let a=&ctx.accounts;\n let pool_updated", " let a=&*ctx.accounts;\n let pool_updated")])
gene('ev_new_creator_local', 'w10r1-admincto-hillclimb genes1', [("new_creator:a.bonding_curve.creator,", "new_creator:target,")])
gene('ev_flags_local', 'w10r1-admincto-hillclimb genes1', [("is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,", "is_holder_reward:holder,is_cashback_coin:cashback,")])
gene('ev_su_flag_early', 'w10r1-admincto-hillclimb genes1', [(POOLSEEDS, " let reset=sharing_update.is_some();" + POOLSEEDS), ("sharing_config_reset:sharing_update.is_some(),", "sharing_config_reset:reset,")])
gene('ev_clock_first', 'w10r1-admincto-hillclimb genes1', [(EV, " let ts=Clock::get()?.unix_timestamp;let e=AdminCtoEvent{timestamp:ts,")])
gene('ev_clock_var', 'w10r1-admincto-hillclimb genes2', [(EV, " let clock=Clock::get()?;let e=AdminCtoEvent{timestamp:clock.unix_timestamp,")])
gene('ev_mint_reload', 'w10r1-admincto-hillclimb genes2', [("authority:a.admin_set_creator_authority.key(),mint,", "authority:a.admin_set_creator_authority.key(),mint:a.mint.key(),")])
gene('ev_fee_local', 'w10r1-admincto-hillclimb genes2', [("new_creator_fee_bps:a.bonding_curve.creator_fee_bps,", "new_creator_fee_bps:fee.unwrap_or(old_fee),")])
gene('ev_bc_key_early', 'w10r1-admincto-hillclimb genes2', [(" let a=&ctx.accounts;\n let pool_updated", " let a=&ctx.accounts;let bc=a.bonding_curve.key();\n let pool_updated"), ("bonding_curve:a.bonding_curve.key(),old_creator", "bonding_curve:bc,old_creator")])

# ---------------- tier 3: y1-cto-blocks / y1-cto-spill / y1-cto-fresh local permutations ----------------
S754 = "  curve.creator=target;\n  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n"
gene('store_perm_BCH', 'y1-cto-blocks t-store-perm-BCH', [(S754, "  curve.is_cashback_coin=cashback;\n  curve.creator=target;\n  curve.is_holder_reward=holder;\n")])
gene('store_perm_HBC', 'y1-cto-blocks t-store-perm-HBC', [(S754, "  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n  curve.creator=target;\n")])
gene('store_perm_BHC', 'y1-cto-blocks t-store-perm-BHC', [(S754, "  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;\n  curve.creator=target;\n")])
gene('store_fee_edit_swap', 'y1-cto-blocks t-store-fee-edit-swap', [("  if let Some(f)=fee{curve.creator_fee_bps=f;}\n  curve.can_edit_creator_fee=false;\n", "  curve.can_edit_creator_fee=false;\n  if let Some(f)=fee{curve.creator_fee_bps=f;}\n")])
gene('tok_polarity', 'y1-cto-blocks s-token-polarity', [("   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{" + CREATE_H + "?;" + TVT + "?;}",
     "   if !frozen{if amount>0{" + CREATE_H + "?;" + TVT + "?;}}else{require!(amount==0,PumpError::CtoSharedVaultFrozen);}")])
gene('w_frozen_polarity', 'y1-cto-blocks w-frozen-polarity', [("if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!(\"Creator quote token account is frozen; fees left in the vaults\");}else{",
     "if !token_frozen(a.current_creator_quote_token_account.as_ref())?{"), ("\n }}Ok(())}\n", "\n }else{msg!(\"Creator quote token account is frozen; fees left in the vaults\");}}Ok(())}\n")])
gene('w_present_order', 'y1-cto-blocks w-present-order', [("  let coin_present=!a.coin_creator_vault_ata.data_is_empty();let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();",
     "  let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();let coin_present=!a.coin_creator_vault_ata.data_is_empty();")])
gene('w_source_present_operands', 'y1-cto-blocks w-source-present-operands', [("let source_present=!collection_native&&!a.creator_vault_quote_token_account.data_is_empty();", "let source_present=!a.creator_vault_quote_token_account.data_is_empty()&&!collection_native;")])
gene('w_frozen_line_swap', 'y1-cto-blocks w-frozen-line-swap / y1-cto-spill coin-frozen-before-source-frozen', [
     ("  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;\n  let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;\n",
      "  let coin_frozen=coin_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;\n  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;\n")])
gene('w_source_frozen_drop_native', 'y1-cto-blocks w-source-frozen-drop-native', [("let source_frozen=!collection_native&&source_present&&token_frozen(", "let source_frozen=source_present&&token_frozen(")])
gene('w_ata_gate_or_rev', 'y1-cto-blocks w-ata-gate-or-rev', [("  if !collection_native||coin_present{", "  if coin_present||!collection_native{")])
gene('w_collect_gate_or_rev', 'y1-cto-blocks w-collect-gate-or-rev', [("  if collection_native||(source_present&&!source_frozen){", "  if (source_present&&!source_frozen)||collection_native{")])
gene('w_collect_gate_and_rev', 'y1-cto-blocks w-collect-gate-and-rev', [("  if collection_native||(source_present&&!source_frozen){", "  if collection_native||(!source_frozen&&source_present){")])
gene('w_coin_gate_and_rev', 'y1-cto-blocks w-coin-gate-and-rev', [("  if coin_present&&!coin_frozen{", "  if !coin_frozen&&coin_present{")])
gene('w_writable_require', 'y1-cto-blocks w-writable-require', [("if !a.current_creator.is_writable{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}", "require!(a.current_creator.is_writable,PumpError::CtoCreatorAccountNotWritable);")])
gene('w_native_eq_rev', 'y1-cto-blocks w-native-eq-rev', [("  let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;", "  let collection_native=anchor_spl::token::spl_token::native_mint::ID==a.quote_mint.key();")])
gene('w_owner_ne_rev', 'y1-cto-blocks w-owner-ne-rev', [("else if a.current_creator.owner!=&anchor_lang::system_program::ID{", "else if &anchor_lang::system_program::ID!=a.current_creator.owner{")])
gene('w_gate_early_return', 'y1-cto-blocks w-collect-old-gate-early-return', [(" if collect_old{wallet(&ctx)?;}", " if !collect_old{}else{wallet(&ctx)?;}")])
gene('w_coin_present_after_native', 'y1-cto-spill wallet-coin-present-before-collection-native (inverse spelling)', [
     ("  let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;\n  let coin_present=!a.coin_creator_vault_ata.data_is_empty();",
      "  let coin_present=!a.coin_creator_vault_ata.data_is_empty();let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;\n  ")])
gene('s_amm_frozen_no_empty', 'y1-cto-blocks s-amm-frozen-no-empty', [("let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(", "let amm_frozen=token_frozen(")])
gene('s_raw_zero_rev', 'y1-cto-blocks s-raw-zero-rev', [("require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,", "require!(0==token_raw_amount(a.coin_creator_vault_ata.as_ref())?,")])
gene('s_native_eq_rev', 'y1-cto-blocks s-native-eq-rev', [(SWEEPSIG + NATIVE, SWEEPSIG + "let native=anchor_spl::token::spl_token::native_mint::ID==a.quote_mint.key();")])
gene('s_native_amount_polarity', 'y1-cto-blocks s-native-amount-polarity', [("   if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;" + NATARM,
     "   if amount==0{Ok(amount)}else{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;"
     "crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&[vaultseeds]).map(|()|amount)}}else{")])
gene('s_amm_else_polarity', 'y1-cto-blocks s-amm-else-polarity', [("  else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(", "  else if a.coin_creator_vault_ata.data_is_empty(){}else{crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(")])
gene('s_dest_before_native', 'y1-cto-spill sweep-dest-before-native', [(SWEEPSIG + NATIVE, SWEEPSIG), ("  let dest=Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID).0;",
     "  let dest=Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID).0;" + NATIVE)])
gene('s_amm_empty_let', 'y1-cto-spill sweep-amm-empty-let', [("let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(", "let amm_empty=a.coin_creator_vault_ata.data_is_empty();let amm_frozen=!amm_empty&&token_frozen("),
     ("else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm", "else if !amm_empty{crate::pump_amm")])
gene('s_bump_inline_temp', 'y1-cto-spill sweep-bump-inline-array-temp', [("let bump=[ctx.bumps.creator_vault];let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&bump];", "let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&[ctx.bumps.creator_vault]];")])
gene('t_pool_eq_rev', 'y1-cto-blocks t-pool-eq-rev', [(" let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();", " let pool_updated=&AMM==a.pool.owner && !a.pool.data_is_empty();")])
gene('t_ev_reset_match', 'y1-cto-blocks t-ev-reset-match', [("sharing_config_reset:sharing_update.is_some(),", "sharing_config_reset:!sharing_update.is_none(),")])
gene('t_sharing_iflet_ref', 'y1-cto-spill sharing-update-if-let-by-ref', [(" if let Some(val)=sharing_update{", " if let Some(val)=&sharing_update{"), ("signer_seeds),val)?;", "signer_seeds),*val)?;")])
gene('t_pool_bump_inline_temp', 'y1-cto-spill pool-bump-inline-array-temp', [(POOLSEEDS, " let poolseeds:&[&[u8]]=&[b\"pool-authority\",mint.as_ref(),&[ctx.bumps.pool_authority]];let signer_seeds:&[&[&[u8]]]=&[poolseeds];")])
gene('t_pool_updated_before_curve', 'y1-cto-spill pool-updated-before-curve-block', [(" let (old_creator,old_fee)={", " let pool_updated=ctx.accounts.pool.owner==&AMM && !ctx.accounts.pool.data_is_empty();let (old_creator,old_fee)={"),
     (" let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();\n", "\n")])
gene('t_old_block_flatten', 'y1-cto-spill old-creator-block-flatten', [(" let (old_creator,old_fee)={\n  let curve=&mut ctx.accounts.bonding_curve;", " {}\n  let curve=&mut ctx.accounts.bonding_curve;"), ("\n (old_creator,old_fee)};\n", "\n \n")])
gene('t_ev_new_creator_prebound', 'y1-cto-spill cto-event-new-creator-prebound', [(EV, " let new_creator=a.bonding_curve.creator;" + EV), ("new_creator:a.bonding_curve.creator,", "new_creator,")])
gene('v_he_and_rev', 'y1-cto-blocks v-he-and-rev', [(" if holder&&!st.holder_reward&&!st.holder_enabled{", " if holder&&!st.holder_enabled&&!st.holder_reward{")])
gene('sp_new_shadow', 'y1-cto-spill new-shadow-let', [(" let a=&ctx.accounts;let mint=a.mint.key();", " let new=new;let a=&ctx.accounts;let mint=a.mint.key();")])
gene('sp_sharing_key_let', 'y1-cto-spill sharing-key-let-before-quote', [(QL, "let sharing=a.sharing_config.key();" + QL), ("new,&holder_key,&a.sharing_config.key())?", "new,&holder_key,&sharing)?")])
gene('sp_swept_first', 'y1-cto-spill swept-declared-first', [(" let swept;\n", "\n"), (" let a=&ctx.accounts;let mint=a.mint.key();", " let swept;let a=&ctx.accounts;let mint=a.mint.key();")])
gene('sp_poolseeds_early', 'y1-cto-spill poolseeds-declared-early', [(POOLSEEDS + "\n", "\n"), (HK, HK + POOLSEEDS.strip())])
gene('sp_validate_new_ref', 'y1-cto-spill validate-new-by-ref', [("new:Option<Pubkey>,holder_key:&Pubkey", "new:&Option<Pubkey>,holder_key:&Pubkey"), ("  let Some(t)=new else{", "  let Some(t)=*new else{"),
     ("validate(&st,holder,fee,new,", "validate(&st,holder,fee,&new,")])
gene('sp_tuple_target_first', 'y1-cto-spill state-tuple-order-target-first', [(OPEN, "let (target,sharing_update,holder,cashback,collect_old)={"), (TUP, "(target,sharing_update,holder,cashback,collect_old)};")])
gene('sp_st_outside_block', 'y1-cto-spill ctostate-outside-tuple-block', [(OPEN + ST, ST + OPEN)])
gene('fr_gate_match_tuple', 'y1-cto-fresh gate-match-tuple', [(GATE, " swept=match (shared,holder){(true,true)=>sweep(&ctx,&holder_key)?,_=>0};")])
gene('fr_swept_result_after_pb', 'y1-cto-fresh question-after-pool-bump', [(GATE, " let swept_r=if shared&&holder{sweep(&ctx,&holder_key)}else{Ok(0)};"),
     (" let pb=[ctx.bumps.pool_authority];", " let pb=[ctx.bumps.pool_authority];swept=swept_r?;")])

gene('validate_inline_always', 'w9r2-admincto-inline iva', [("fn validate(st:", "#[inline(always)] fn validate(st:")])
gene('wallet_inline_always', 'w9r2-admincto-inline iwa', [("fn wallet(ctx:", "#[inline(always)] fn wallet(ctx:")])
gene('sweep_inline_always', 'w9r2-admincto-inline isa', [("fn sweep(ctx:", "#[inline(always)] fn sweep(ctx:")])
gene('fee_range_sibling', 'w9r2-admincto-sibling v3 (pump-amm admin_cto_pool spelling)', [("if f==0||f>st.max_fee{", "if !(f>0&&f<=st.max_fee){")])
gene('hr_nested_if', 'w9r2-admincto-sibling v5 (holder-reward immutability nested)', [(" if st.holder_reward&&!holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}", " if st.holder_reward{if !holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}")])

# ---------------- wave-12 peer genes (applied on main b5975fa = #2749 k4size) ----------------
PAD13 = "// layout-pad(13): aligns the next Source site with the original line\n\n"
gene('amm_cb_local', 'w12a11-cto-sibling t18 (pump-amm admin_cto_pool per-arm is_cashback_coin local)', [(PAD13, PAD13.replace("\n\n", "\n let cashback=if holder{false}else{st.cashback};\n")),
     ("  if !holder&&st.cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}", "  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}")])
gene('amm_cb_arms', 'w12a11-cto-sibling t19 (cashback returned from the target arms)', [
     (" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{", " let (target,cashback)=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}(*holder_key,false)}else{"),
     ("  if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}t};", "  if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}(t,st.cashback)};"),
     ("  if !holder&&st.cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}", "  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}")])
gene('oldfee_after_cb', 'w12a11-cto-sibling t17 (old fee read after the creator/holder/cashback stores, AMM order)', [
     ("let old_fee=curve.creator_fee_bps;let old_creator=curve.creator;curve.can_edit_creator_fee=false;", "let old_creator=curve.creator;curve.can_edit_creator_fee=false;"),
     ("  curve.is_cashback_coin=cashback;\n", "  curve.is_cashback_coin=cashback;let old_fee=curve.creator_fee_bps;\n")])

NM753 = "  let curve=&mut ctx.accounts.bonding_curve;let old_fee=curve.creator_fee_bps;let old_creator=curve.creator;curve.can_edit_creator_fee=false;\n"
gene('fee_unwrap_revert', 'w12a04-cto-k4size p_feeunwrap_revert (branchy if-let fee store, as the original)', [("  curve.creator_fee_bps=fee.unwrap_or(old_fee);\n", "  if let Some(f)=fee{curve.creator_fee_bps=f;}\n")])
gene('canedit_revert', 'w12a04-cto-k4size p_canedit_revert (can_edit stored last, as the original)', [(NM753, NM753.replace("curve.can_edit_creator_fee=false;", "")),
     ("  curve.creator_fee_bps=fee.unwrap_or(old_fee);\n\n", "  curve.creator_fee_bps=fee.unwrap_or(old_fee);\n  curve.can_edit_creator_fee=false;\n")])
gene('oldfee_revert', 'w12a04-cto-k4size p_oldfee_revert (old_creator read before old_fee)', [("let old_fee=curve.creator_fee_bps;let old_creator=curve.creator;curve.can_edit", "let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;curve.can_edit")])
gene('store_orig', 'w12a13-cto-sizeknobs finding: original store order creator, cashback, holder, if-let fee, can_edit last', [
     (NM753 + "  curve.creator=target;\n  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n  curve.creator_fee_bps=fee.unwrap_or(old_fee);\n\n",
      NM753.replace("curve.can_edit_creator_fee=false;", "") + "  curve.creator=target;\n  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;\n  if let Some(f)=fee{curve.creator_fee_bps=f;}\n  curve.can_edit_creator_fee=false;\n")])

GENES = G


def apply(text, names):
    for n in names:
        if not n:
            continue
        for old, new in G[n]:
            if old.count('\n') != new.count('\n'):
                raise ValueError(f'gene {n}: newline count changes')
            c = text.count(old)
            if c != 1:
                raise ValueError(f'gene {n}: old occurs {c}x: {old[:70]!r}')
            text = text.replace(old, new)
    return text


if __name__ == '__main__':
    import sys
    base = open(sys.argv[1]).read()
    bad = []
    for n in G:
        try:
            apply(base, [n])
        except ValueError as e:
            bad.append(str(e))
    print(len(G), 'genes;', len(bad), 'do not apply')
    for b in bad:
        print(' ', b)
