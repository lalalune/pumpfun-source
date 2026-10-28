#!/usr/bin/env python3
"""closures.py <crate dir>: write the arithmetic whose Overflow/Truncation errors the original raises from
separate 520-B closure functions as inline `ok_or_else(|| error!(..))` / `map_err(|_| error!(..))` closures
(coordfiles lane).  Evidence per edit is the original parent window's code around the closure call.
  sell_v2.rs   341 T  quote = u64::try_from(amount*vq/(vt+amount))            (0x144508 +0x1498, after lib.rs:2454 helper)
               366 O  quote - protocol_fee  /  368 O  (quote - pf) - creator_fee   (0x144508 +0x1668/+0x16e0)
  migrate.rs   280 O  real_quote_reserves + post_complete_quote_in  / 282 O  - pool_migration_fee   (0x3fb70 +0x940/+0x980:
               `r7 = [bc+0x60] + [bc+0x98]` = Account<BondingCurve> +0x60 real_quote_reserves, +0x98 post_complete_quote_in)
  migrate_v2.rs 309 O same checked add (unconditional), 313 O native-only checked_sub of the fee (0x49888 +0xf98/+0x1010)
Also splits sell_v2's three entry checks onto their own lines (whitespace only; orig 243/245/247).
"""
import sys
from pathlib import Path
S = Path(sys.argv[1]) / 'src'
def rep(p, old, new):
    f = S / p; t = f.read_text()
    assert t.count(old) == 1, (p, old[:90], t.count(old))
    f.write_text(t.replace(old, new))
rep('sell_v2.rs', ' require!(!c.complete,PumpError::BondingCurveComplete);require_gt!(amount,0,PumpError::SellZeroAmount);require_gte!(a.associated_base_user.amount,amount,PumpError::NotEnoughTokensToSell);\n',
    ' require!(!c.complete,PumpError::BondingCurveComplete);\n require_gt!(amount,0,PumpError::SellZeroAmount);\n require_gte!(a.associated_base_user.amount,amount,PumpError::NotEnoughTokensToSell);\n')
rep('sell_v2.rs', ' let quote=narrow(amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128+amount as u128))?;\n',
    ' let quote=u64::try_from(amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128+amount as u128)).map_err(|_|error!(PumpError::Truncation))?;\n')
rep('sell_v2.rs', 'let pf=initial_protocol_fee;let cf=initial_creator_fee;let output=sub(sub(quote,pf)?,cf)?;\n',
    'let pf=initial_protocol_fee;let cf=initial_creator_fee;\n let output=quote.checked_sub(pf)\n  .ok_or_else(||error!(PumpError::Overflow))?\n  .checked_sub(cf)\n  .ok_or_else(||error!(PumpError::Overflow))?;\n')
rep('migrate.rs', ' let quote=real_quote.checked_sub(fee).ok_or_else(||error!(PumpError::Overflow))?;\n',
    ' let quote=real_quote.checked_add(a.bonding_curve.post_complete_quote_in)\n  .ok_or_else(||error!(PumpError::Overflow))?\n  .checked_sub(fee)\n  .ok_or_else(||error!(PumpError::Overflow))?;\n')
rep('migrate_v2.rs', ' let quote=if native{real_quote.checked_sub(fee).ok_or_else(||error!(PumpError::Overflow))?}else{real_quote};\n',
    ' let quote=real_quote.checked_add(a.bonding_curve.post_complete_quote_in)\n  .ok_or_else(||error!(PumpError::Overflow))?;\n let quote=if native{quote.checked_sub(fee).ok_or_else(||error!(PumpError::Overflow))?}else{quote};\n')
print('closures applied')
