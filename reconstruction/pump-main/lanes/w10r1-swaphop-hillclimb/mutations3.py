"""Mutation set 3 = set 2 + sibling-lane findings as composable seeds + extra families.

Composite mutations: old/new may be tuples of strings, applied pairwise in order.
Sibling seeds (credited to their lanes; re-measured here in combination):
  sib-require-gt       w7r1-swaphop-frame : require_gt!(base,0,BuyZeroAmount) (Le not rewritten by
                                            SimplifyComparisonIntegral -> continue block created first)
  sib-raw-match        w7r1-swaphop-frame : raw_output adds match &post_fill {Some(p)=>p.base_out,None=>0}
  sib-buyback-noguard  w7r1-swaphop-coords: no paid_buyback != 0 guard (mhc_transfer_buyback_out returns Ok for 0)
"""
import mutations2 as base

M = list(base.M)


def m(mid, old, new):
    if isinstance(old, tuple):
        for o, n in zip(old, new):
            assert o.count("\n") == n.count("\n"), mid
    else:
        assert old.count("\n") == new.count("\n"), mid
    M.append((mid, old, new))


m("sib-require-gt",
  "if base == 0 { return Err(error!(PumpError::BuyZeroAmount).with_values((base,0))); }",
  "require_gt!(base,0,PumpError::BuyZeroAmount);")
m("sib-require-gt-reversed",
  "if base == 0 { return Err(error!(PumpError::BuyZeroAmount).with_values((base,0))); }",
  "if base <= 0 { return Err(error!(PumpError::BuyZeroAmount).with_values((base,0))); }")
RAW = ("let (base_amount,quote_amount,pf,cf,post_out) = if base > reserves {",
       "                    (reserves,quote,fees.protocol_fee,fees.creator_fee,post.base_out)\n                }else{post_fill=None;(reserves,q,pf,cf,0)}\n            }else{post_fill=None;(base,q,pf,cf,0)};")
RAWN = ("let (base_amount,quote_amount,pf,cf) = if base > reserves {",
        "                    (reserves,quote,fees.protocol_fee,fees.creator_fee)\n                }else{post_fill=None;(reserves,q,pf,cf)}\n            }else{post_fill=None;(base,q,pf,cf)};")
m("sib-raw-match", RAW + ("let raw_output = base_amount.checked_add(post_out).ok_or_else(",),
  RAWN + ("let raw_output = base_amount.checked_add(match &post_fill{Some(p)=>p.base_out,None=>0}).ok_or_else(",))
m("raw-match-swapped", RAW + ("let raw_output = base_amount.checked_add(post_out).ok_or_else(",),
  RAWN + ("let raw_output = match &post_fill{Some(p)=>p.base_out,None=>0}.checked_add(base_amount).ok_or_else(",))
m("raw-map-or", RAW + ("let raw_output = base_amount.checked_add(post_out).ok_or_else(",),
  RAWN + ("let raw_output = base_amount.checked_add(post_fill.as_ref().map_or(0,|p| p.base_out)).ok_or_else(",))
m("raw-if-let", RAW + ("let raw_output = base_amount.checked_add(post_out).ok_or_else(",),
  RAWN + ("let raw_output = base_amount.checked_add(if let Some(p)=&post_fill {p.base_out} else {0}).ok_or_else(",))
m("raw-match-copy", RAW + ("let raw_output = base_amount.checked_add(post_out).ok_or_else(",),
  RAWN + ("let raw_output = base_amount.checked_add(match post_fill{Some(p)=>p.base_out,None=>0}).ok_or_else(",))
m("sib-buyback-noguard",
  "            } else if paid_buyback != 0 {\n                transfer_buyback_out(",
  "            } else {\n                transfer_buyback_out(")
m("c-deref-once",
  "        let c = &h.bonding_curve;\n        let fee_config_len",
  "        let c = &*h.bonding_curve;\n        let fee_config_len")
m("c-deref-twice",
  "        let c = &h.bonding_curve;\n        let fee_config_len",
  "        let c: &Account<BondingCurve> = &h.bonding_curve;\n        let fee_config_len")
m("reserves-after-compare",
  "let reserves = c.real_token_reserves; let (base_amount,quote_amount,pf,cf",
  "let (base_amount,quote_amount,pf,cf")
M.pop()  # breaks references to reserves
m("sell-require-gt-if",
  "            require_gt!(net,0,PumpError::SellZeroAmount);",
  "            if net <= 0 { return Err(error!(PumpError::SellZeroAmount).with_values((net,0))); }")
m("payout-if-nested",
  "        if native && !buy && last {\n            crate::trade::quote_payments::pay_out_native(&h.bonding_curve,a.user.to_account_info(),output)?;\n        }",
  "        if native && !buy { if last {\n            crate::trade::quote_payments::pay_out_native(&h.bonding_curve,a.user.to_account_info(),output)?;\n        } }")
m("completed-eq-false",
  "let completed=h.bonding_curve.real_token_reserves==0; if completed {",
  "let completed=h.bonding_curve.real_token_reserves<=0; if completed {")
m("hop-vault-clone-ref",
  "vault: if buy { h.associated_base_bonding_curve.to_account_info() } else { h.associated_quote_bonding_curve.to_account_info() } }) }",
  "vault: if buy { AsRef::<AccountInfo>::as_ref(&*h.associated_base_bonding_curve).clone() } else { h.associated_quote_bonding_curve.to_account_info() } }) }")
m("sell-net-require-gt-first",
  "            require_gt!(net,0,PumpError::SellZeroAmount);",
  "            require!(net > 0,PumpError::SellZeroAmount);")
M.pop()  # different error payload (no values): behaviour change

# ---- pure statement reorders (no fallible call changes order) ---------------------------
SEEDS = "        let seeds: &[&[&[u8]];1] = &[&[b\"bonding-curve\",h.base_mint.to_account_info().key.as_ref(),&[curve_bump]]];\n        let c = &h.bonding_curve;\n"
m("seeds-after-c", SEEDS,
  "        let c = &h.bonding_curve;\n        let seeds: &[&[&[u8]];1] = &[&[b\"bonding-curve\",h.base_mint.to_account_info().key.as_ref(),&[curve_bump]]];\n")
m("seeds-after-cap",
  (SEEDS, "let cap = crate::buy_fee_market_cap(c,&h.base_mint)?;\n"),
  ("\n        let c = &h.bonding_curve;\n", "let cap = crate::buy_fee_market_cap(c,&h.base_mint)?; let seeds: &[&[&[u8]];1] = &[&[b\"bonding-curve\",h.base_mint.to_account_info().key.as_ref(),&[curve_bump]]];\n"))
m("seeds-before-buy",
  (SEEDS, "        let buy = if *current_mint"),
  ("\n        let c = &h.bonding_curve;\n", "        let seeds: &[&[&[u8]];1] = &[&[b\"bonding-curve\",h.base_mint.to_account_info().key.as_ref(),&[curve_bump]]]; let buy = if *current_mint"))
m("c-before-buy",
  ("        let c = &h.bonding_curve;\n        let fee_config_len", "        let buy = if *current_mint"),
  ("\n        let fee_config_len", "        let c = &h.bonding_curve; let buy = if *current_mint"))
m("curve-key-first",
  ("let curve_key = h.bonding_curve.key(); require_ata(", "let native = h.bonding_curve.quote_mint == Pubkey::default();"),
  ("require_ata(", "let curve_key = h.bonding_curve.key(); let native = h.bonding_curve.quote_mint == Pubkey::default();"))
m("curve-key-after-native",
  ("let curve_key = h.bonding_curve.key(); require_ata(", "let native = h.bonding_curve.quote_mint == Pubkey::default();"),
  ("require_ata(", "let native = h.bonding_curve.quote_mint == Pubkey::default(); let curve_key = h.bonding_curve.key();"))
m("fee-config-len-before-c",
  ("        let c = &h.bonding_curve;\n        let fee_config_len = a.fee_config.to_account_info().data_len(); let cap",),
  ("        let fee_config_len = a.fee_config.to_account_info().data_len(); let c = &h.bonding_curve;\n        let cap",))
