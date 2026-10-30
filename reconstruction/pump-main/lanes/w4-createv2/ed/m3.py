EDITS=[(" let virtual_quote_reserves=if quote_mint==sol {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};\n",
" let mut virtual_quote_reserves=global.initial_virtual_sol_reserves;if quote_mint!=sol {virtual_quote_reserves=reserves.unwrap_or(initial_virtual_quote_reserves);}\n")]
