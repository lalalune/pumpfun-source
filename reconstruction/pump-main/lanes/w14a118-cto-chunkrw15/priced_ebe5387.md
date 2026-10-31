| trial | rewrite | bytes | M (Δ) | ratio | skM (Δ) | note |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| rw1 | sweep head sibling style: (dest,_) destructure + require_keys_eq! ConstraintSeeds + amm_frozen as if-expr | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| rw2 | sweep token arm plain ? sequence: create_idempotent(..)?;transfer_vault_tokens(..)?;return Ok(amount) | 27,456 | 2,133 (-114) | 0.63834 | 2,712 (-98) |  |
| rw3 | sweep native arm collect_creator_fee sibling style: let rent=Rent::get()?;let min=..;if amount>0{ensure?;transfer_native?;}Ok(amount) | 27,400 | 1,349 (-898) | 0.40413 | 2,425 (-385) |  |
| rw6 | post-validate tuple join as match (shared,holder){(true,true),(true,false),(false,_)} | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| rw6b | post-validate tuple join with !shared arm first (if !shared{..}else if holder{..}else{..}) | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| rw7 | wallet coin CPI gate as if do_coin | 27,400 | 2,239 (-8) | 0.67076 | 2,811 (+1) |  |
| rw5 | whole sweep clean-room sibling style: rw1+rw2+rw3 | 27,432 | 1,289 (-958) | 0.38593 | 2,347 (-463) |  |
| rw8 | whole sweep clean-room (rw5) + wallet if do_coin | 27,440 | 1,289 (-958) | 0.38587 | 2,348 (-462) |  |
| rw1a | sweep dest check as (dest,_) + require_keys_eq! | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| rw3a | sweep native arm: let rent=Rent::get()?;let min=rent.minimum_balance(0) (no block) | 27,368 | 1,956 (-291) | 0.58633 | 2,473 (-337) |  |
| t1 | t1 (w14a89/w14a109) re-run: shared-arm test new.is_none() | 27,376 | 2,246 (-1) | 0.67316 | 2,807 (-3) |  |
| t1rw7 | t1 + wallet coin CPI gate as if do_coin | 27,376 | 2,241 (-6) | 0.67166 | 2,808 (-2) |  |
| rw7b | wallet coin region: do_coin as if coin_present{!frozen?}else{false} + gate if do_coin | 27,400 | 2,239 (-8) | 0.67076 | 2,811 (+1) |  |
| rw7c | wallet do_coin as if coin_present{!frozen?}else{false} (gate kept coin_present&do_coin) | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| n5 | native arm: Rent::get() as explicit match Ok/Err(e.into()) | 27,352 | 2,221 (-26) | 0.66597 | 2,804 (-6) |  |
| n3 | native arm: amount computed in one block {let min={rent..};lamports.saturating_sub(min)} | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| n8 | native arm: lamports bound to a local before saturating_sub | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| n7 | native arm: Rent::get().map(\|rent\|rent.minimum_balance(0))? | 27,416 | 2,225 (-22) | 0.66637 | 2,805 (-5) |  |
| n9 | native arm: checked_sub(min).unwrap_or(0) instead of saturating_sub | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| ev2 | event sharing_config_reset bound before the sharing match (is_some at the match site) | 27,392 | 2,242 (-5) | 0.67176 | 2,810 (+0) |  |
| ev1 | event: curve fields through let curve=&a.bonding_curve | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
| s1 | sweep native test computed after the dest check | 27,392 | 2,225 (-22) | 0.66667 | 2,793 (-17) |  |
| s1b | sweep native test computed after the amm/TCF block, before vsigner | 27,376 | 2,021 (-226) | 0.60572 | 2,788 (-22) |  |
| j1 | drop the Ok::<_,Error>((target,sharing_update,cashback))? hop after the tuple block | 27,400 | 1,838 (-409) | 0.55063 | 2,807 (-3) |  |
| w3 | wallet create_idempotent gate as coin_present\|\|!collection_native | 27,400 | 2,229 (-18) | 0.66777 | 2,789 (-21) |  |
| w4 | wallet coin_present computed before collection_native | 27,408 | 2,209 (-38) | 0.66167 | 2,781 (-29) |  |
| pa1 | pool CPI args passed directly (no pargs tuple): target, curve.is_holder_reward, fee | 27,432 | 2,108 (-139) | 0.63114 | 2,706 (-104) |  |
| k1 | swept as a plain let at the sweep call (no deferred init) | 27,400 | 2,247 (+0) | 0.67316 | 2,810 (+0) | token-identical to main |
