"""Line-preserving, behaviour-preserving spelling mutations of multi_hop_curve::swap_hop.

Each mutation is (id, old, new): `old` must occur exactly once in the current file text,
and `old`/`new` contain the same number of newlines, so every line!() immediate stays put.
Mutations only respell code (operand order of commutative/pure operations, short-circuit
order of side-effect-free conditions, binding vs inline temporaries, if/else polarity,
match vs if-let, method vs free fn); none changes what the program does on any input.
"""

M = []


def m(mid, old, new):
    assert old.count("\n") == new.count("\n"), mid
    M.append((mid, old, new))


# --- prologue -------------------------------------------------------------------------
m("mayhem-eq-false",
  "require!(!h.bonding_curve.is_mayhem_mode,PumpError::MultiHopMayhemCurveNotSupported);",
  "require!(h.bonding_curve.is_mayhem_mode == false,PumpError::MultiHopMayhemCurveNotSupported);")
m("native-default-lhs",
  "let native = h.bonding_curve.quote_mint == Pubkey::default();",
  "let native = Pubkey::default() == h.bonding_curve.quote_mint;")
m("native-eq-method",
  "let native = h.bonding_curve.quote_mint == Pubkey::default();",
  "let native = h.bonding_curve.quote_mint.eq(&Pubkey::default());")
m("quote-fee-polarity",
  "let quote_fee = if native { None } else { crate::transfer_fee_recovered::get_transfer_fee(&h.quote_mint.to_account_info())? };",
  "let quote_fee = if !native { crate::transfer_fee_recovered::get_transfer_fee(&h.quote_mint.to_account_info())? } else { None };")
m("quote-fee-match",
  "let quote_fee = if native { None } else { crate::transfer_fee_recovered::get_transfer_fee(&h.quote_mint.to_account_info())? };",
  "let quote_fee = match native { true => None, false => crate::transfer_fee_recovered::get_transfer_fee(&h.quote_mint.to_account_info())? };")
m("quote-fee-ai-bind",
  "let quote_fee = if native { None } else { crate::transfer_fee_recovered::get_transfer_fee(&h.quote_mint.to_account_info())? };",
  "let quote_fee = if native { None } else { let qi = h.quote_mint.to_account_info(); crate::transfer_fee_recovered::get_transfer_fee(&qi)? };")
m("base-prog-asref-once",
  "token_program_for(&a.token_program, &a.token_2022_program, h.base_mint.as_ref().as_ref())?",
  "token_program_for(&a.token_program, &a.token_2022_program, AsRef::<AccountInfo>::as_ref(&*h.base_mint))?")
m("quote-prog-asref-once",
  "token_program_for(&a.token_program, &a.token_2022_program, h.quote_mint.as_ref().as_ref())?",
  "token_program_for(&a.token_program, &a.token_2022_program, AsRef::<AccountInfo>::as_ref(&*h.quote_mint))?")
m("require-ata-base-keys-bound",
  "require_ata(&h.associated_base_bonding_curve.key(), &curve_key, &h.base_mint.key(), &base_token_program.key())?;",
  "{ let k = h.associated_base_bonding_curve.key(); let mk = h.base_mint.key(); require_ata(&k, &curve_key, &mk, &base_token_program.key())?; }")
m("require-ata-quote-keys-bound",
  "require_ata(&h.associated_quote_bonding_curve.key(), &curve_key, &h.quote_mint.key(), &quote_token_program.key())?;",
  "{ let k = h.associated_quote_bonding_curve.key(); let mk = h.quote_mint.key(); require_ata(&k, &curve_key, &mk, &quote_token_program.key())?; }")
m("admit-native-polarity",
  "if !native { crate::buy_v2::admit_associated_token_account(h.associated_quote_bonding_curve.as_ref(), &h.bonding_curve.to_account_info(), h.quote_mint.key(), quote_token_program.key(), &h.quote_mint.to_account_info(), &quote_token_program, false, a.user.as_ref(), a.system_program.as_ref())?; } else { require_ata(&h.associated_quote_bonding_curve.key(), &curve_key, &h.quote_mint.key(), &quote_token_program.key())?; }",
  "if native { require_ata(&h.associated_quote_bonding_curve.key(), &curve_key, &h.quote_mint.key(), &quote_token_program.key())?; } else { crate::buy_v2::admit_associated_token_account(h.associated_quote_bonding_curve.as_ref(), &h.bonding_curve.to_account_info(), h.quote_mint.key(), quote_token_program.key(), &h.quote_mint.to_account_info(), &quote_token_program, false, a.user.as_ref(), a.system_program.as_ref())?; }")
m("buyback-validate-flag-eq1",
  "        if flag & 1 != 0 {\n            crate::trade::validate_buyback_fee_recipient_account(",
  "        if flag & 1 == 1 {\n            crate::trade::validate_buyback_fee_recipient_account(")

# --- direction / seeds ----------------------------------------------------------------
m("buy-deref-rhs",
  "let buy = if *current_mint == h.quote_mint.key() { true } else if *current_mint == h.base_mint.key() { false } else { return err!(PumpError::MultiHopDiscontinuousPath) };",
  "let buy = if h.quote_mint.key() == *current_mint { true } else if h.base_mint.key() == *current_mint { false } else { return err!(PumpError::MultiHopDiscontinuousPath) };")
m("buy-ref-compare",
  "let buy = if *current_mint == h.quote_mint.key() { true } else if *current_mint == h.base_mint.key() { false } else { return err!(PumpError::MultiHopDiscontinuousPath) };",
  "let buy = if current_mint == &h.quote_mint.key() { true } else if current_mint == &h.base_mint.key() { false } else { return err!(PumpError::MultiHopDiscontinuousPath) };")
m("buy-match-guard",
  "let buy = if *current_mint == h.quote_mint.key() { true } else if *current_mint == h.base_mint.key() { false } else { return err!(PumpError::MultiHopDiscontinuousPath) };",
  "let buy = match *current_mint { m if m == h.quote_mint.key() => true, m if m == h.base_mint.key() => false, _ => return err!(PumpError::MultiHopDiscontinuousPath) };")
m("seeds-key-method",
  "h.base_mint.to_account_info().key.as_ref()",
  "h.base_mint.to_account_info().key.as_ref()")  # placeholder (identity, dropped below)
M.pop()
m("fee-config-len-after-cap",
  "let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = crate::buy_fee_market_cap(c,&h.base_mint)?;",
  "let cap = crate::buy_fee_market_cap(c,&h.base_mint)?; let fee_config_len = a.fee_config.to_account_info().data_len();")
m("fee-config-ai-bind",
  "let fee_config_len = a.fee_config.to_account_info().data_len();",
  "let fee_config_ai = a.fee_config.to_account_info(); let fee_config_len = fee_config_ai.data_len();")
m("trade-amount-polarity",
  "        let trade_amount = if buy {\n            crate::transfer_fee_recovered::post_fee_amount(&quote_fee,amount)?\n        }else{amount};",
  "        let trade_amount = if !buy { amount } else {\n            crate::transfer_fee_recovered::post_fee_amount(&quote_fee,amount)?\n        };")
m("entry-sub-ok-or-match",
  "        amount.checked_sub(trade_amount).ok_or_else(|| error!(PumpError::Overflow))?;",
  "        if amount.checked_sub(trade_amount).is_none() { return Err(error!(PumpError::Overflow)); }")
m("entry-sub-lt-compare",
  "        amount.checked_sub(trade_amount).ok_or_else(|| error!(PumpError::Overflow))?;",
  "        if amount < trade_amount { return Err(error!(PumpError::Overflow)); }")

# --- buy arm --------------------------------------------------------------------------
m("buy-prate-eq0",
  "            let p_rate = if flag & 1 != 0 { selected.protocol_fee_bps } else { 0 };\n            let c_rate = if flag & 2 != 0 { selected.creator_fee_bps } else { 0 };\n            let (_,",
  "            let p_rate = if flag & 1 == 0 { 0 } else { selected.protocol_fee_bps };\n            let c_rate = if flag & 2 == 0 { 0 } else { selected.creator_fee_bps };\n            let (_,")
m("buy-crate-before-prate",
  "            let p_rate = if flag & 1 != 0 { selected.protocol_fee_bps } else { 0 };\n            let c_rate = if flag & 2 != 0 { selected.creator_fee_bps } else { 0 };\n            let (_,",
  "            let c_rate = if flag & 2 != 0 { selected.creator_fee_bps } else { 0 };\n            let p_rate = if flag & 1 != 0 { selected.protocol_fee_bps } else { 0 };\n            let (_,")
m("buy-post-fill-decl-late",
  "            let post_fill; let selected = crate::legacy_sell::fee_math::get_fees(&a.global,c,&a.fee_config,fee_config_len,cap,trade_amount)?;",
  "            let selected = crate::legacy_sell::fee_math::get_fees(&a.global,c,&a.fee_config,fee_config_len,cap,trade_amount)?; let post_fill;")
m("buy-net-quote-bind-fees",
  "let (_,crate::trade::TradeFees{protocol_fee:pf,creator_fee:cf,..}) = crate::trade::net_quote_for_budget(&c.creator,p_rate,c_rate,trade_amount)?;",
  "let (_,budget_fees) = crate::trade::net_quote_for_budget(&c.creator,p_rate,c_rate,trade_amount)?; let (pf,cf) = (budget_fees.protocol_fee,budget_fees.creator_fee);")
m("buy-tokens-bind",
  "let base = u64::try_from(crate::constant_product::tokens_for_quote(c,q)?).map_err(|_| error!(PumpError::Truncation))?;",
  "let tokens = crate::constant_product::tokens_for_quote(c,q)?; let base = u64::try_from(tokens).map_err(|_| error!(PumpError::Truncation))?;")
m("buy-tokens-try-into",
  "let base = u64::try_from(crate::constant_product::tokens_for_quote(c,q)?).map_err(|_| error!(PumpError::Truncation))?;",
  "let base: u64 = crate::constant_product::tokens_for_quote(c,q)?.try_into().map_err(|_| error!(PumpError::Truncation))?;")
m("buy-base-zero-eq-lhs",
  "if base == 0 { return Err(error!(PumpError::BuyZeroAmount).with_values((base,0))); }",
  "if 0 == base { return Err(error!(PumpError::BuyZeroAmount).with_values((base,0))); }")
m("buy-reserves-lt",
  "let (base_amount,quote_amount,pf,cf,post_out) = if base > reserves {",
  "let (base_amount,quote_amount,pf,cf,post_out) = if reserves < base {")
m("buy-reserves-inline",
  "let reserves = c.real_token_reserves; let (base_amount,quote_amount,pf,cf,post_out) = if base > reserves {",
  "let (base_amount,quote_amount,pf,cf,post_out) = if base > c.real_token_reserves { let reserves = c.real_token_reserves;")
m("buy-complete-fill-match",
  "                if let Some((fees, quote, post)) = complete_fill(",
  "                if let Some((fees, quote, post)) = complete_fill(")
M.pop()
m("buy-post-fill-some-ref",
  "                    post_fill=Some(post);\n",
  "                    post_fill=Some(post.clone());\n")
M.pop()  # behaviour-identical but adds clone; drop
m("buy-raw-output-swap",
  "let raw_output = base_amount.checked_add(post_out).ok_or_else(|| error!(PumpError::Overflow))?;",
  "let raw_output = post_out.checked_add(base_amount).ok_or_else(|| error!(PumpError::Overflow))?;")
m("buy-raw-output-match",
  "let raw_output = base_amount.checked_add(post_out).ok_or_else(|| error!(PumpError::Overflow))?;",
  "let raw_output = match base_amount.checked_add(post_out) { Some(v) => v, None => return Err(error!(PumpError::Overflow)) };")
m("buy-transfer-polarity",
  "if native { crate::user_quote_payments::transfer_native(a.system_program.as_ref(),&a.user,h.bonding_curve.as_ref(),amount)?; } else { transfer_input(a,previous,&quote_token_program,&h.associated_quote_bonding_curve,h.quote_mint.decimals,AsRef::<AccountInfo>::as_ref(&*h.quote_mint),amount)?; }",
  "if !native { transfer_input(a,previous,&quote_token_program,&h.associated_quote_bonding_curve,h.quote_mint.decimals,AsRef::<AccountInfo>::as_ref(&*h.quote_mint),amount)?; } else { crate::user_quote_payments::transfer_native(a.system_program.as_ref(),&a.user,h.bonding_curve.as_ref(),amount)?; }")
m("buy-transfer-quote-asref-method",
  "transfer_input(a,previous,&quote_token_program,&h.associated_quote_bonding_curve,h.quote_mint.decimals,AsRef::<AccountInfo>::as_ref(&*h.quote_mint),amount)?;",
  "transfer_input(a,previous,&quote_token_program,&h.associated_quote_bonding_curve,h.quote_mint.decimals,h.quote_mint.as_ref().as_ref(),amount)?;")
m("buy-tuple-sub-wrapping",
  "raw_output,amount - trade_amount,post_fill)",
  "raw_output,amount.wrapping_sub(trade_amount),post_fill)")
m("buy-fees-struct-order",
  "            (crate::trade::TradeFees{protocol_fee:pf,creator_fee:cf,protocol_fee_bps:p_rate,creator_fee_bps:c_rate},base_amount,quote_amount,raw_output,",
  "            (crate::trade::TradeFees{protocol_fee_bps:p_rate,creator_fee_bps:c_rate,protocol_fee:pf,creator_fee:cf},base_amount,quote_amount,raw_output,")

# --- sell arm -------------------------------------------------------------------------
m("sell-gross-bind",
  "let gross_sell = u64::try_from(c.sell_quote(amount)?).map_err(|_| error!(PumpError::Truncation))?;",
  "let quote = c.sell_quote(amount)?; let gross_sell = u64::try_from(quote).map_err(|_| error!(PumpError::Truncation))?;")
m("sell-gross-try-into",
  "let gross_sell = u64::try_from(c.sell_quote(amount)?).map_err(|_| error!(PumpError::Truncation))?;",
  "let gross_sell: u64 = c.sell_quote(amount)?.try_into().map_err(|_| error!(PumpError::Truncation))?;")
m("sell-rates-eq0",
  "            let p_rate = if flag & 1 != 0 { selected.protocol_fee_bps } else { 0 };\n            let c_rate = if flag & 2 != 0 { selected.creator_fee_bps } else { 0 };\n            let pf =",
  "            let p_rate = if flag & 1 == 0 { 0 } else { selected.protocol_fee_bps };\n            let c_rate = if flag & 2 == 0 { 0 } else { selected.creator_fee_bps };\n            let pf =")
m("sell-fees-eq0",
  "            let pf = if flag & 1 != 0 { selected.protocol_fee } else { 0 };\n            let cf = if flag & 2 != 0 { selected.creator_fee } else { 0 };",
  "            let pf = if flag & 1 == 0 { 0 } else { selected.protocol_fee };\n            let cf = if flag & 2 == 0 { 0 } else { selected.creator_fee };")
m("sell-fees-before-rates",
  "            let p_rate = if flag & 1 != 0 { selected.protocol_fee_bps } else { 0 };\n            let c_rate = if flag & 2 != 0 { selected.creator_fee_bps } else { 0 };\n            let pf = if flag & 1 != 0 { selected.protocol_fee } else { 0 };\n            let cf = if flag & 2 != 0 { selected.creator_fee } else { 0 };",
  "            let pf = if flag & 1 != 0 { selected.protocol_fee } else { 0 };\n            let cf = if flag & 2 != 0 { selected.creator_fee } else { 0 };\n            let p_rate = if flag & 1 != 0 { selected.protocol_fee_bps } else { 0 };\n            let c_rate = if flag & 2 != 0 { selected.creator_fee_bps } else { 0 };")
m("sell-rates-tuple",
  "            let p_rate = if flag & 1 != 0 { selected.protocol_fee_bps } else { 0 };\n            let c_rate = if flag & 2 != 0 { selected.creator_fee_bps } else { 0 };\n            let pf = if flag & 1 != 0 { selected.protocol_fee } else { 0 };\n            let cf = if flag & 2 != 0 { selected.creator_fee } else { 0 };",
  "            let (p_rate,pf) = if flag & 1 != 0 { (selected.protocol_fee_bps,selected.protocol_fee) } else { (0,0) };\n            let (c_rate,cf) = if flag & 2 != 0 { (selected.creator_fee_bps,selected.creator_fee) } else { (0,0) };\n\n")
m("sell-net-check-is-none",
  "            net.checked_sub(output).ok_or_else(|| error!(PumpError::Overflow))?;",
  "            if net.checked_sub(output).is_none() { return Err(error!(PumpError::Overflow)); }")
m("sell-transfer-base-asref-method",
  "transfer_input(a,previous,&base_token_program,&h.associated_base_bonding_curve.to_account_info(),h.base_mint.decimals,AsRef::<AccountInfo>::as_ref(&*h.base_mint),amount)?;",
  "transfer_input(a,previous,&base_token_program,&h.associated_base_bonding_curve.to_account_info(),h.base_mint.decimals,h.base_mint.as_ref().as_ref(),amount)?;")
m("sell-transfer-vault-asref",
  "transfer_input(a,previous,&base_token_program,&h.associated_base_bonding_curve.to_account_info(),",
  "transfer_input(a,previous,&base_token_program,AsRef::<AccountInfo>::as_ref(&*h.associated_base_bonding_curve),")
m("sell-quote-out-cond-native-first",
  "if last && !native && net != 0 {",
  "if !native && last && net != 0 {")
m("sell-quote-out-cond-net-first",
  "if last && !native && net != 0 {",
  "if net != 0 && last && !native {")
m("sell-quote-out-cond-nested",
  "if last && !native && net != 0 { transfer_quote_out(&quote_token_program,&h.associated_quote_bonding_curve,&a.destination,&h.bonding_curve,h.quote_mint.decimals,AsRef::<AccountInfo>::as_ref(&*h.quote_mint),net,seeds)?; }",
  "if last && !native { if net != 0 { transfer_quote_out(&quote_token_program,&h.associated_quote_bonding_curve,&a.destination,&h.bonding_curve,h.quote_mint.decimals,AsRef::<AccountInfo>::as_ref(&*h.quote_mint),net,seeds)?; } }")
m("sell-tuple-sub-wrapping",
  "output,net - output,None)",
  "output,net.wrapping_sub(output),None)")

# --- fee accrual / buyback ------------------------------------------------------------
m("post-fill-ref-pattern",
  "let post_buyback_raw = if let Some(post)=post_fill.as_ref() {",
  "let post_buyback_raw = if let Some(post)=&post_fill {")
m("post-fill-match",
  "let post_buyback_raw = if let Some(post)=post_fill.as_ref() {",
  "let post_buyback_raw = if let Some(ref post)=post_fill {")
m("post-fill-quote-first",
  "            h.bonding_curve.post_complete_base_out=post.base_out;\n            h.bonding_curve.post_complete_quote_in=post.quote_in;",
  "            h.bonding_curve.post_complete_quote_in=post.quote_in;\n            h.bonding_curve.post_complete_base_out=post.base_out;")
m("paid-buyback-swap",
  "let paid_buyback=buyback_raw.checked_add(post_buyback_raw).ok_or_else(",
  "let paid_buyback=post_buyback_raw.checked_add(buyback_raw).ok_or_else(")
m("post-buyback-before-received",
  "let received_buyback=crate::transfer_fee_recovered::post_fee_amount(&quote_fee,paid_buyback)?;\n        let post_buyback=crate::transfer_fee_recovered::post_fee_amount(&quote_fee,post_buyback_raw)?;",
  "let post_buyback=crate::transfer_fee_recovered::post_fee_amount(&quote_fee,post_buyback_raw)?;\n        let received_buyback=crate::transfer_fee_recovered::post_fee_amount(&quote_fee,paid_buyback)?;")
m("buyback-flag-eq1",
  "        if flag & 1 != 0 {\n            if native {",
  "        if flag & 1 == 1 {\n            if native {")
m("buyback-native-polarity",
  "            if native {\n                native_buyback(a,event_bump,&h.bonding_curve,paid_buyback)?;\n            } else if paid_buyback != 0 {",
  "            if !native { if paid_buyback != 0 {\n                native_buyback(a,event_bump,&h.bonding_curve,paid_buyback)?;\n            } } else if paid_buyback != 0 {")
M.pop()  # wrong semantics; removed
m("payout-cond-order-buy-first",
  "if native && !buy && last {",
  "if !buy && native && last {")
m("payout-cond-order-last-first",
  "if native && !buy && last {",
  "if last && native && !buy {")
m("payout-user-ai-ref",
  "pay_out_native(&h.bonding_curve,a.user.to_account_info(),output)?;",
  "pay_out_native(&h.bonding_curve,AsRef::<AccountInfo>::as_ref(&*a.user).clone(),output)?;")

# --- events / output ------------------------------------------------------------------
m("clock-bind",
  "let timestamp = Clock::get()?.unix_timestamp;",
  "let clock = Clock::get()?; let timestamp = clock.unix_timestamp;")
m("event-keys-bound",
  "&a.user.key(),&h.base_mint.key(),buy,",
  "&user_key,&mint_key,buy,")
M.pop()  # needs a let; see event-keys-let
m("event-keys-let",
  "let timestamp = Clock::get()?.unix_timestamp; let event = trade_event(c,&a.global,&crate::UserVolumeAccumulator::default(),&a.user.key(),&h.base_mint.key(),buy,",
  "let timestamp = Clock::get()?.unix_timestamp; let user_key = a.user.key(); let mint_key = h.base_mint.key(); let event = trade_event(c,&a.global,&crate::UserVolumeAccumulator::default(),&user_key,&mint_key,buy,")
m("uva-bind",
  "let event = trade_event(c,&a.global,&crate::UserVolumeAccumulator::default(),",
  "let uva = crate::UserVolumeAccumulator::default(); let event = trade_event(c,&a.global,&uva,")
m("completed-inline",
  "let completed=h.bonding_curve.real_token_reserves==0; if completed {",
  "if h.bonding_curve.real_token_reserves==0 {")
m("c-rebind-direct",
  "        let c = &h.bonding_curve;\n        let timestamp",
  "        let c = &*h.bonding_curve;\n        let timestamp")
m("hop-output-mint-bind",
  "Ok(HopOutput { mint: if buy { h.base_mint.key() } else { h.quote_mint.key() }, amount: output,",
  "let mint = if buy { h.base_mint.key() } else { h.quote_mint.key() }; Ok(HopOutput { mint, amount: output,")
m("hop-output-vault-bind",
  "vault: if buy { h.associated_base_bonding_curve.to_account_info() } else { h.associated_quote_bonding_curve.to_account_info() } }) }",
  "vault: (if buy { &h.associated_base_bonding_curve } else { &h.associated_quote_bonding_curve }).to_account_info() }) }")
m("hop-output-polarity",
  "Ok(HopOutput { mint: if buy { h.base_mint.key() } else { h.quote_mint.key() }, amount: output, buyback_fee: received_buyback, vault: if buy { h.associated_base_bonding_curve.to_account_info() } else { h.associated_quote_bonding_curve.to_account_info() } }) }",
  "Ok(HopOutput { mint: if !buy { h.quote_mint.key() } else { h.base_mint.key() }, amount: output, buyback_fee: received_buyback, vault: if !buy { h.associated_quote_bonding_curve.to_account_info() } else { h.associated_base_bonding_curve.to_account_info() } }) }")
m("completion-key-order",
  "let completion=crate::trade_types::CompleteEvent { mint:h.base_mint.key(),user:a.user.key(),",
  "let completion=crate::trade_types::CompleteEvent { user:a.user.key(),mint:h.base_mint.key(),")
m("main-arm-tuple-is-buy-polarity",
  "        let (fees,base_amount,quote_amount,output,adapter_difference,post_fill) = if buy {",
  "        let (fees,base_amount,quote_amount,output,adapter_difference,post_fill) = if buy == true {")
