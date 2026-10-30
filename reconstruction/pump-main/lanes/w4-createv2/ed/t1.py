EDITS=[(" let virtual_quote_reserves=if quote_mint==Pubkey::default() {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};",
" let q=(quote_mint,reserves);let virtual_quote_reserves=if q.0==Pubkey::default() {global.initial_virtual_sol_reserves} else {q.1.unwrap_or(initial_virtual_quote_reserves)};"),
(" bonding_curve.quote_mint=quote_mint;"," bonding_curve.quote_mint=q.0;")]
