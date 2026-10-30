"""Mutation set 4 = set 3 (w7r1-swaphop-hillclimb, re-applied to the x1-p2 base) + wave-10 targets.

All mutations are line-preserving (same newline count per old/new pair) and
behaviour-preserving respellings. Composite mutations take tuples applied pairwise.
New families target the x1-p2 base (buy arm keeps TradeFees whole) and the residuals
named by sibling lanes:
  cap-*   : region-1 lane (#2526) -- the &BondingCurve GEP for buy_fee_market_cap should be
            computed before the fee_config AccountInfo clone (spill-slot pair -0xaa8/-0xab0).
  nf-*    : the whole TradeFees `nf` from net_quote_for_budget.
  res-*   : the reserves-if tuple (region-3 lane: le-first moved only the overflow closure).
"""
import mutations3 as base

M = list(base.M)


def m(mid, old, new):
    if isinstance(old, tuple):
        for o, n in zip(old, new):
            assert o.count("\n") == n.count("\n"), mid
    else:
        assert old.count("\n") == new.count("\n"), mid
    M.append((mid, old, new))


CAP = "let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = match crate::buy_fee_market_cap(c,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };"
m("cap-helper-plain", CAP,
  "fn len_cap(fee_config: &Account<'_, crate::pump_fees::accounts::FeeConfig>, curve: &BondingCurve, mint: &Mint) -> Result<(usize, u128)> { let len = fee_config.to_account_info().data_len(); let cap = match crate::buy_fee_market_cap(curve,mint) { Ok(v) => v, Err(e) => return Err(e) }; Ok((len, cap)) } let (fee_config_len, cap) = len_cap(&a.fee_config, c, &h.base_mint)?;")
m("cap-helper-inline", CAP,
  "#[inline] fn len_cap(fee_config: &Account<'_, crate::pump_fees::accounts::FeeConfig>, curve: &BondingCurve, mint: &Mint) -> Result<(usize, u128)> { let len = fee_config.to_account_info().data_len(); let cap = match crate::buy_fee_market_cap(curve,mint) { Ok(v) => v, Err(e) => return Err(e) }; Ok((len, cap)) } let (fee_config_len, cap) = len_cap(&a.fee_config, c, &h.base_mint)?;")
m("cap-helper-len-only", CAP,
  "fn cfg_len(fee_config: &Account<'_, crate::pump_fees::accounts::FeeConfig>, curve: &BondingCurve) -> (usize, &BondingCurve) { (fee_config.to_account_info().data_len(), curve) } let (fee_config_len, cc) = cfg_len(&a.fee_config, c); let cap = match crate::buy_fee_market_cap(cc,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };")
m("cap-curve-tuple", CAP,
  "let cap_in: (&BondingCurve, &Mint) = (c, &h.base_mint); let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = match crate::buy_fee_market_cap(cap_in.0,cap_in.1) { Ok(v) => v, Err(e) => return Err(e) };")
m("cap-curve-ref-let", CAP,
  "let cc: &BondingCurve = &***c; let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = match crate::buy_fee_market_cap(cc,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };")
m("cap-curve-asref", CAP,
  "let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = match crate::buy_fee_market_cap(c.as_ref(),&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };")
m("cap-closure", CAP,
  "let cap_of = |m: &Mint| crate::buy_fee_market_cap(c, m); let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = match cap_of(&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };")
m("cap-len-ai-bind", CAP,
  "let fee_config_info = a.fee_config.to_account_info(); let fee_config_len = fee_config_info.data_len(); drop(fee_config_info); let cap = match crate::buy_fee_market_cap(c,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };")
m("cap-len-block", CAP,
  "let fee_config_len = { a.fee_config.to_account_info().data_len() }; let cap = match crate::buy_fee_market_cap(c,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };")
m("cap-len-asref-clone", CAP,
  "let fee_config_len = AccountInfo::clone(AsRef::<AccountInfo>::as_ref(&**a.fee_config)).data_len(); let cap = match crate::buy_fee_market_cap(c,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };")
m("cap-question", CAP,
  "let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = crate::buy_fee_market_cap(c,&h.base_mint)?;")
m("cap-mint-deref", CAP,
  "let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = match crate::buy_fee_market_cap(c,&**h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };")
m("cap-mint-first-bind", CAP,
  "let base_mint: &Mint = &h.base_mint; let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = match crate::buy_fee_market_cap(c,base_mint) { Ok(v) => v, Err(e) => return Err(e) };")

# --- nf (whole TradeFees from net_quote_for_budget) ----------------------------------
NQ = "let (_,nf) = crate::trade::net_quote_for_budget(&c.creator,p_rate,c_rate,trade_amount)?;"
m("nf-dot1", NQ, "let nf = crate::trade::net_quote_for_budget(&c.creator,p_rate,c_rate,trade_amount)?.1;")
m("nf-match", NQ, "let (_,nf) = match crate::trade::net_quote_for_budget(&c.creator,p_rate,c_rate,trade_amount) { Ok(v) => v, Err(e) => return Err(e) };")
m("nf-bind-all", NQ, "let (_net,nf) = crate::trade::net_quote_for_budget(&c.creator,p_rate,c_rate,trade_amount)?;")
SUB = "let q = crate::trade::sub3(trade_amount,nf.protocol_fee,nf.creator_fee)?;"
m("nf-sub3-bind", SUB, "let (npf,ncf) = (nf.protocol_fee,nf.creator_fee); let q = crate::trade::sub3(trade_amount,npf,ncf)?;")
m("nf-sub3-match", SUB, "let q = match crate::trade::sub3(trade_amount,nf.protocol_fee,nf.creator_fee) { Ok(v) => v, Err(e) => return Err(e) };")

# --- reserves-if tuple -----------------------------------------------------------------
RIF = "let reserves = c.real_token_reserves; let (base_amount,quote_amount,fees,post_fill) = if base > reserves {"
REL = "            }else{(base,q,nf,None)};"
m("res-le-first", (RIF, REL),
  ("let reserves = c.real_token_reserves; let (base_amount,quote_amount,fees,post_fill) = if base <= reserves { (base,q,nf,None) } else {",
   "            };"))
m("res-lt-rhs", RIF,
  "let reserves = c.real_token_reserves; let (base_amount,quote_amount,fees,post_fill) = if reserves < base {")
m("res-inline-field", RIF,
  "let (base_amount,quote_amount,fees,post_fill) = if base > c.real_token_reserves { let reserves = c.real_token_reserves;")
m("res-ge-not", RIF,
  "let reserves = c.real_token_reserves; let (base_amount,quote_amount,fees,post_fill) = if !(base <= reserves) {")
CF = ("                if let Some((f, quote, post)) = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,",
      "                    (reserves,quote,f,Some(post))\n                }else{(reserves,q,nf,None)}")
m("cf-match", CF,
  ("                match complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,",
   "                    Some((f, quote, post)) => (reserves,quote,f,Some(post)),\n                None => (reserves,q,nf,None) }"))
m("cf-match-none-first", CF,
  ("                match complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,",
   "                    None => (reserves,q,nf,None),\n                Some((f, quote, post)) => (reserves,quote,f,Some(post)) }"))
m("cf-map-or", CF,
  ("                if let Some((f, quote, post)) = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,",
   "                    (reserves,quote,f,Some(post))\n                }else{(reserves,q,nf,None)}"))  # identity placeholder (dropped below)
M.pop()
m("cf-bind-result", CF[0],
  "                let filled = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,")
# cf-bind-result needs the `{` after `?` changed too; composite form:
M.pop()
CFQ = ("                if let Some((f, quote, post)) = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,",
       "                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)? {")
m("cf-bind-result", CFQ,
  ("                let filled = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,",
   "                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)?; if let Some((f, quote, post)) = filled {"))
m("cf-curve-asref", CFQ,
  ("                if let Some((f, quote, post)) = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,&h.bonding_curve,",
   CFQ[1]))
m("cf-fields-tuple", CF,
  ("                if let Some((f, quote, post)) = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,",
   "                    (reserves,quote,crate::trade::TradeFees{..f},Some(post))\n                }else{(reserves,q,nf,None)}"))

# --- buy-arm tail -----------------------------------------------------------------------
TAIL = "            (fees,base_amount,quote_amount,raw_output,amount - trade_amount,post_fill)"
m("tail-fees-rebuild", TAIL,
  "            (crate::trade::TradeFees{..fees},base_amount,quote_amount,raw_output,amount - trade_amount,post_fill)")
m("tail-diff-bind", TAIL,
  "            {let d = amount - trade_amount; (fees,base_amount,quote_amount,raw_output,d,post_fill)}")
m("tail-diff-wrapping", TAIL,
  "            (fees,base_amount,quote_amount,raw_output,amount.wrapping_sub(trade_amount),post_fill)")

# --- w9r1 d1 halves (adapter_difference bound from the line-571 checked_sub) -------------
CS = "        amount.checked_sub(trade_amount).ok_or_else(|| error!(PumpError::Overflow))?;"
m("adbind", (CS, TAIL),
  ("        let adapter_difference = amount.checked_sub(trade_amount).ok_or_else(|| error!(PumpError::Overflow))?;",
   "            (fees,base_amount,quote_amount,raw_output,adapter_difference,post_fill)"))

# --- y1-hop-llvm fee_inputs helper (#[inline(always)], curve first): fixes the -0xaa8/-0xab0 swap at -16 B
m("cap-fee-inputs-always", CAP,
  "#[inline(always)] fn fee_inputs(curve: &BondingCurve, fee_config: &Account<'_, crate::pump_fees::accounts::FeeConfig>, mint: &Mint) -> Result<(usize, u128)> { let len = fee_config.to_account_info().data_len(); let cap = crate::buy_fee_market_cap(curve,mint)?; Ok((len, cap)) } let (fee_config_len, cap) = match fee_inputs(c,&a.fee_config,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };")
m("cap-fee-inputs-always-q", CAP,
  "#[inline(always)] fn fee_inputs(curve: &BondingCurve, fee_config: &Account<'_, crate::pump_fees::accounts::FeeConfig>, mint: &Mint) -> Result<(usize, u128)> { let len = fee_config.to_account_info().data_len(); let cap = match crate::buy_fee_market_cap(curve,mint) { Ok(v) => v, Err(e) => return Err(e) }; Ok((len, cap)) } let (fee_config_len, cap) = fee_inputs(c,&a.fee_config,&h.base_mint)?;")
