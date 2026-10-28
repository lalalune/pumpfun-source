#!/usr/bin/env python3
"""closures7.py <crate dir> (after closures3.py/S3): v3 pool-side transfer-fee gross-up helper.
  trade_v3.rs 382 O  transfer fee = gross - net after the gross-up, inside the shared v3 fee helper the original
                     has at trade_v3.rs:~360-388 (0x80df8: x checked at :371/:375, gross-up via util/transfer_fee.rs:66,
                     then `jlt gross, x` -> closure 0x81640 at :382; called from buy_v3 and buy_exact_quote_in_v3).
Ours computed `fee` then `pool_quote = net + fee` inline in both v3 buy handlers; both now call
`gross_up_quote` (placed before `add`, as the original helper precedes add at :390), which re-derives the fee
from the gross exactly as the original does.  Values and errors unchanged.
"""
import sys
from pathlib import Path
S = Path(sys.argv[1]) / 'src'
f = S / 'trade_v3.rs'; t = f.read_text()
old = ('    let quote_transfer_fee=if is_sol{0}else{quote_fee_for_amount(&quote_fee,net_pool_quote,true)?};\n'
       '    let pool_quote=add(net_pool_quote,quote_transfer_fee)?;\n')
assert t.count(old) == 2, t.count(old)
t = t.replace(old, '    let (pool_quote,quote_transfer_fee)=gross_up_quote(&quote_fee,is_sol,net_pool_quote)?;\n')
add_line = 'fn add(a:u64,b:u64)->Result<u64>{a.checked_add(b).ok_or_else(||error!(PumpError::Overflow))}\n'
assert t.count(add_line) == 1
helper = ('/// Gross-up of the pool-side quote by the quote mint\'s transfer fee; the fee is re-derived from the gross.\n'
          '#[inline(always)]\n'
          'fn gross_up_quote(quote_fee:&Option<(u64,u64,u64)>,is_sol:bool,net:u64)->Result<(u64,u64)>{\n'
          '    let gross=add(net,if is_sol{0}else{quote_fee_for_amount(quote_fee,net,true)?})?;\n'
          '    let quote_transfer_fee=gross.checked_sub(net).ok_or_else(||error!(PumpError::Overflow))?;\n'
          '    Ok((gross,quote_transfer_fee))\n'
          '}\n')
t = t.replace(add_line, helper + add_line)
f.write_text(t)
print('closures7 applied')
