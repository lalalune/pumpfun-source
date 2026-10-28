#!/usr/bin/env python3
"""closures3.py <crate dir>: buy_exact_quote_in_v3 closures (coordfiles lane).
  trade_v3.rs 911 T  tokens out for the net quote budget      (orig 0x1489f8 +0x850: W0xa0838 then high word != 0)
              930 T  quote for the capped amount (exceeds)    (orig 0x1489f8 +0xf90: after the lib.rs:2428 helper)
              970 O  transfer_base = amount + post_base        (orig 0x1489f8 +0x1a58 checked add, then :971 BuySlippage check)
"""
import sys
from pathlib import Path
S = Path(sys.argv[1]) / 'src'
def rep(p, old, new):
    f = S / p; t = f.read_text()
    assert t.count(old) == 1, (p, old[:90], t.count(old))
    f.write_text(t.replace(old, new))
rep('trade_v3.rs', '    let computed_amount=narrow(curve.virtual_token_reserves as u128*effective as u128/(curve.virtual_quote_reserves as u128+effective as u128))?;\n',
    '    let computed_amount=u64::try_from(curve.virtual_token_reserves as u128*effective as u128/(curve.virtual_quote_reserves as u128+effective as u128)).map_err(|_|error!(PumpError::Truncation))?;\n')
rep('trade_v3.rs', '    let quote=if exceeds{narrow(curve.real_token_reserves as u128*curve.virtual_quote_reserves as u128/(curve.virtual_token_reserves as u128-curve.real_token_reserves as u128))?.checked_add(1)',
    '    let quote=if exceeds{u64::try_from(curve.real_token_reserves as u128*curve.virtual_quote_reserves as u128/(curve.virtual_token_reserves as u128-curve.real_token_reserves as u128)).map_err(|_|error!(PumpError::Truncation))?.checked_add(1)')
rep('trade_v3.rs', '    let transfer_base=add(amount,post_base)?;\n    if !(exceeds && (curve.is_mayhem_mode || is_fee_exempt) && partial_fill){',
    '    let transfer_base=amount.checked_add(post_base).ok_or_else(||error!(PumpError::Overflow))?;\n    if !(exceeds && (curve.is_mayhem_mode || is_fee_exempt) && partial_fill){')
print('closures3 applied')
