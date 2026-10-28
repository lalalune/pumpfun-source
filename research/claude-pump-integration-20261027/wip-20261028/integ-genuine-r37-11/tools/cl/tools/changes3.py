#!/usr/bin/env python3
"""coordlib round 2, step 3 (after changes2.py; line-neutral edits inside lib.rs, can run before or after layout.py):
  * Global::add_quote_mint / remove_quote_mint: the slot search is a `for` loop with an early `return Ok(())` and the
    error after the loop (orig 0x9a190 / 0x9ac28 place the 6066 / 6068 error block right after the loop; the
    `find().ok_or_else(..)?` and let-else forms put it at the end of the function, 8 bytes longer).
Usage: changes3.py <crate dir>
"""
import sys
from pathlib import Path
p = Path(sys.argv[1]) / 'src/lib.rs'
t = p.read_text()
a_old = "let slot=self.whitelisted_quote_mints.iter_mut().find(|key|**key==Pubkey::default()).ok_or_else(||error!(PumpError::QuoteMintWhitelistFull))?;*slot=quote_mint;Ok(())"
a_new = "for slot in self.whitelisted_quote_mints.iter_mut(){if *slot==Pubkey::default(){*slot=quote_mint;return Ok(());}} err!(PumpError::QuoteMintWhitelistFull)"
r_old = "let slot=self.whitelisted_quote_mints.iter_mut().find(|key|**key==quote_mint).ok_or_else(||error!(PumpError::QuoteMintNotWhitelisted))?;*slot=Pubkey::default();Ok(())"
r_new = "for slot in self.whitelisted_quote_mints.iter_mut(){if *slot==quote_mint{*slot=Pubkey::default();return Ok(());}} err!(PumpError::QuoteMintNotWhitelisted)"
assert t.count(a_old) == 1 and t.count(r_old) == 1
p.write_text(t.replace(a_old, a_new).replace(r_old, r_new))
print('changes3 applied')
