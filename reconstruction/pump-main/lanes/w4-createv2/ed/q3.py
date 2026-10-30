import runpy
EDITS=runpy.run_path('ed/r1nc.py')['EDITS']+[
("if quote_mint==Pubkey::default() {global.initial_virtual_sol_reserves}","if quote_mint.to_bytes()==[0;32] {global.initial_virtual_sol_reserves}")]
