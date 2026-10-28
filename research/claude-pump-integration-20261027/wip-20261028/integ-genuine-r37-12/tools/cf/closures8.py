#!/usr/bin/env python3
"""closures8.py <crate dir> (after closures3.py / split_buy_v2.py): fee-exempt token-out truncations.
The original buy_exact handlers compute the tokens out for a whitelisted (fee-exempt) user in their own branch,
with their own Truncation closure, before the fee-adjusted path:
  buy_v2.rs  881 T  (orig 0x13f630 +0x1be8: whitelist memcmp -> W0xa0838 tokens-out -> high word != 0) ; :927 = normal path
  trade_v3.rs 904 T (orig 0x1489f8 +0xa28: whitelist memcmp -> W0xa0838 -> trunc)                     ; :911 = normal path
For an exempt user our fee terms are all 0, so the token amount is the same expression; the branch only gives the
exempt path its own closure (identical value and error code on both paths).
"""
import sys
from pathlib import Path
S = Path(sys.argv[1]) / 'src'
def rep(p, old, new):
    f = S / p; t = f.read_text()
    assert t.count(old) == 1, (p, old[:90], t.count(old))
    f.write_text(t.replace(old, new))
E2 = 'u64::try_from(c.virtual_token_reserves as u128*e as u128/(c.virtual_quote_reserves as u128+e as u128)).map_err(|_|error!(PumpError::Truncation))?'
rep('buy_v2.rs', '  ' + E2 + '};\n',
    '  if a.user.key()==a.global.whitelist_pda{' + E2 + '}\n  else{' + E2 + '}};\n')
E3 = 'u64::try_from(curve.virtual_token_reserves as u128*effective as u128/(curve.virtual_quote_reserves as u128+effective as u128)).map_err(|_|error!(PumpError::Truncation))?'
rep('trade_v3.rs', '    let computed_amount=' + E3 + ';\n',
    '    let computed_amount=if is_fee_exempt{' + E3 + '}\n        else{' + E3 + '};\n')
print('closures8 applied')
