#!/usr/bin/env python3
"""closures5.py <crate dir>: multi-hop per-hop executor closures (orig window 0x5b3b0, multi_hop_curve_swap.rs).
  571 O  buy hop: quote transfer fee = amount - net trade amount      (0x5b3b0 +0x1930, `jlt input, net` after util/transfer_fee.rs:56)
  589 T  buy hop: base out u64::try_from(..), followed by :590 BuyZeroAmount   (0x5b3b0 +0x21b0)
  624 O  buy hop with post-complete fill: capped + post_base          (0x5b3b0 +0x28c0 checked add)
  692 O  sell hop: quote transfer fee = raw output - net output        (0x5b3b0 +0x1cf0 after util/transfer_fee.rs:56)
The receipt's adapter difference (emitted as unparsed_trailing_field) is taken from these two fees, which are
exactly quote_before_adapter - quote_after_adapter of the previous code (values unchanged).
"""
import sys
from pathlib import Path
S = Path(sys.argv[1]) / 'src'
def rep(p, old, new):
    f = S / p; t = f.read_text()
    assert t.count(old) == 1, (p, old[:90], t.count(old))
    f.write_text(t.replace(old, new))
M = 'multi_hop_curve_swap.rs'
rep(M, '            sub(amount,crate::trade::quote_transfer_fee(&h.quote_mint.to_account_info(),amount,false)?)?\n        }else{amount};\n',
       '            sub(amount,crate::trade::quote_transfer_fee(&h.quote_mint.to_account_info(),amount,false)?)?\n        }else{amount};\n'
       '        let buy_transfer_fee = amount.checked_sub(trade_amount).ok_or_else(|| error!(PumpError::Overflow))?;\n')
rep(M, '            let base = n(div(effective as u128 * c.virtual_token_reserves as u128,\n                c.virtual_quote_reserves as u128 + effective as u128)?)?;\n',
       '            let base = u64::try_from(div(effective as u128 * c.virtual_token_reserves as u128, c.virtual_quote_reserves as u128 + effective as u128)?).map_err(|_| error!(PumpError::Truncation))?;\n')
rep(M, '(capped,first_quote,first_protocol,first_creator,add(capped,post_base)?)',
       '(capped,first_quote,first_protocol,first_creator,capped.checked_add(post_base).ok_or_else(|| error!(PumpError::Overflow))?)')
rep(M, '            sub(raw_output,crate::trade::quote_transfer_fee(&h.quote_mint.to_account_info(),raw_output,false)?)?\n        }else{raw_output};\n'
       '        let quote_before_adapter = if buy { amount } else { raw_output };\n        let quote_after_adapter = if buy { trade_amount } else { output };\n',
       '            sub(raw_output,crate::trade::quote_transfer_fee(&h.quote_mint.to_account_info(),raw_output,false)?)?\n        }else{raw_output};\n'
       '        let sell_transfer_fee = raw_output.checked_sub(output).ok_or_else(|| error!(PumpError::Overflow))?;\n')
rep(M, '        let adapter_difference = sub(quote_before_adapter,quote_after_adapter)?;\n',
       '        let adapter_difference = if buy { buy_transfer_fee } else { sell_transfer_fee };\n')
print('closures5 applied')
