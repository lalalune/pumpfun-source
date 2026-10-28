#!/usr/bin/env python3
"""extra_genuine.py <crate dir>: genuine deliveries of other lanes folded into the integ-layout composite (line-neutral).
  bodyloB-01 (base r37g4, +0x56658): migrate_v2::refund_pool_authority builds the signer seeds as one nested temporary
  passed to an inlined transfer closure (seed temporaries in the original frame order, system_program loaded after them).
"""
import sys
from pathlib import Path
S = Path(sys.argv[1]) / 'src'
f = S / 'migrate_v2.rs'; t = f.read_text()
old = (" let mint=a.base_mint.key();let bump=[bump];let signer_seeds:&[&[&[u8]];1]=&[&[b\"pool-authority\",mint.as_ref(),&bump]];\n"
       " crate::migrate::transfer_native(a.system_program.as_ref(),&a.pool_authority,destination,amount,signer_seeds)\n")
new = (" let transfer=|signer_seeds:&[&[&[u8]];1]|crate::migrate::transfer_native(a.system_program.as_ref(),&a.pool_authority,destination,amount,signer_seeds);\n"
       " transfer(&[&[b\"pool-authority\",a.base_mint.key().as_ref(),&[bump]]])\n")
assert t.count(old) == 1, t.count(old)
f.write_text(t.replace(old, new))
print('extra_genuine applied (bodyloB-01)')
