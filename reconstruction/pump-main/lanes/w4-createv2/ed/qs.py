import runpy
EDITS=runpy.run_path('ed/r1nc.py')['EDITS']+[
("\n\npub fn execute<'info>","\nfn is_sol_quote(quote_mint:Pubkey)->bool{quote_mint==Pubkey::default()}\npub fn execute<'info>"),
("if quote_mint==Pubkey::default() {global.initial_virtual_sol_reserves}","if is_sol_quote(quote_mint) {global.initial_virtual_sol_reserves}")]
