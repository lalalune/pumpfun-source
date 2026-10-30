EDITS=[(" let initial_virtual_quote_reserves=global.initial_virtual_quote_reserves;\n let virtual_quote_reserves=if quote_mint==Pubkey::default() {",
" let is_sol=quote_mint==Pubkey::default();\n let initial_virtual_quote_reserves=global.initial_virtual_quote_reserves;\n let virtual_quote_reserves=if is_sol {")]
