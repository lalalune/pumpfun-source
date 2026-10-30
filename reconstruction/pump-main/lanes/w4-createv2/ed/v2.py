import runpy
EDITS=runpy.run_path('ed/r1nc.py')['EDITS']+[
("\n\npub fn execute<'info>","\nfn initial_virtual_quote_reserves(global:&Global,quote_mint:&Pubkey,reserves:Option<u64>)->u64{if *quote_mint==Pubkey::default() {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(global.initial_virtual_quote_reserves)}}\npub fn execute<'info>"),
(" let virtual_quote_reserves=if quote_mint==Pubkey::default() {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(global.initial_virtual_quote_reserves)};"," let virtual_quote_reserves=initial_virtual_quote_reserves(global,&quote_mint,reserves);")]
