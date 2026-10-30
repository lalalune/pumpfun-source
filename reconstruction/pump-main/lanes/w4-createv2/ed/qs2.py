import runpy
EDITS=runpy.run_path('ed/qs.py')['EDITS'][:-2]+[
("\n\npub fn execute<'info>","\n#[inline(always)]fn is_sol_quote(quote_mint:Pubkey)->bool{quote_mint==Pubkey::default()}\npub fn execute<'info>"),
("if quote_mint==Pubkey::default() {global.initial_virtual_sol_reserves}","if is_sol_quote(quote_mint) {global.initial_virtual_sol_reserves}")]
