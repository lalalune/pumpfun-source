#!/usr/bin/env python3
"""closures4.py <crate dir> (after split_buy_v2.py): buy_exact_quote_in_v2 transfer-fee closure.
  buy_v2.rs 995 O  transfer fee re-derived as gross - quote after the BuySlippage check (orig :986)
            (orig 0x13f630 +0x28d0: `jlt [gross], quote` after the W0x173d8 total-cost helper whose gross-up is
             util/transfer_fee.rs:66) - same pattern as the buy path's :469.  Values unchanged.
"""
import sys
from pathlib import Path
S = Path(sys.argv[1]) / 'src'
def rep(p, old, new):
    f = S / p; t = f.read_text()
    assert t.count(old) == 1, (p, old[:90], t.count(old))
    f.write_text(t.replace(old, new))
rep('buy_v2.rs',
    ' let quote_transfer_fee=if native{0}else{crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),quote,true)?};\n'
    ' let gross_quote=add(quote,quote_transfer_fee)?;\n'
    ' if !(partial && computed>c.real_token_reserves){require_gte!(amount,limit,PumpError::BuySlippageBelowMinTokensOut);}\n',
    ' let pre_quote_transfer_fee=if native{0}else{crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),quote,true)?};\n'
    ' let gross_quote=add(quote,pre_quote_transfer_fee)?;\n'
    ' if !(partial && computed>c.real_token_reserves){require_gte!(amount,limit,PumpError::BuySlippageBelowMinTokensOut);}\n'
    ' let quote_transfer_fee=gross_quote.checked_sub(quote).ok_or_else(||error!(PumpError::Overflow))?;\n')
print('closures4 applied')
