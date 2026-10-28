#!/usr/bin/env python3
"""integ_genuine.py <crate dir>: genuine changes made by the integ-layout lane itself (after round3.py, lane patches, ext798.py).
  1. the four original callers of the sell quote helper use BondingCurve::sell_quote (added by ext798.py; it replaced
     this lane's byte-identical free fn) - the helper itself: `sell_quote(curve, amount) -> Result<u128>` = amount * virtual_quote / (virtual_token + amount) with the
     DivisionByZero require! (orig 0xa0538, lib.rs:2454, the sibling of buy_quote 0xa0070 at 2428/2430 in the original's
     bonding-curve math region).  Evidence: 0xa0538 (768 B) adds vt [curve+0x40] + amount as u128, requires it != 0
     (6026), multiplies amount by vq [curve+0x48] (__multi3) and divides (__udivti3), returning Ok(u128); its callers are
     the sell paths that then narrow with a Truncation closure: sell_v2 0x144508 (+0x1498, sell_v2.rs:341), sell_v3
     0x14a8a8 (+0x640, trade_v3.rs:1140), the multi-hop sell hop 0x5b3b0 (+0x1970, :673) and the legacy sell 0x152888
     (lib.rs:981).  Ours computed the quote inline at those four sites; they now call sell_quote (same value; the zero
     denominator is unreachable there because amount > 0 is required first, and where it was reachable it now returns
     DivisionByZero like the original instead of a division panic / the multi-hop div() error, same code 6026).
  2. creator/migrate_bonding_curve_creator.rs: the two require!s of execute on their own lines (they shared one line),
     so that after pump-big-lo's body patch (0x37e08 coordinate-only) the layout can put them on the original lines
     46 / 53 (integ_anchors.json).  Formatting only.
  3. PR #362 (research/pump-feeconfig-decoder-recovery, merged on main as fbd81e77d): the route's FeeConfig is its own Rust
     type in trade_types.rs (same six ordered fields, Borsh + Clone derives) instead of an alias of the generated
     pump_fees::accounts::FeeConfig, so the generated account's Borsh reader has one caller and is inlined into its
     unchecked decoder again (orig 0x1159d8, 1,176 B). The removed alias line is kept blank (coordinates unchanged).
"""
import sys
from pathlib import Path
S = Path(sys.argv[1]) / 'src'
def rd(p): return (S / p).read_text()
def wr(p, t): (S / p).write_text(t)
def rep(t, old, new, n=1, what=''):
    assert t.count(old) == n, (what or old[:80], t.count(old), n)
    return t.replace(old, new)

t = rd('lib.rs')
t = rep(t, "let quote=u64::try_from(amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128+amount as u128)).map_err(|_|error!(PumpError::Truncation))?;",
        "let quote=u64::try_from(c.sell_quote(amount)?).map_err(|_|error!(PumpError::Truncation))?;", what='legacy sell quote')
wr('lib.rs', t)
t = rd('sell_v2.rs')
t = rep(t, "let quote=u64::try_from(amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128+amount as u128)).map_err(|_|error!(PumpError::Truncation))?;",
        "let quote=u64::try_from(c.sell_quote(amount)?).map_err(|_|error!(PumpError::Truncation))?;", what='sell_v2 quote')
wr('sell_v2.rs', t)
t = rd('trade_v3.rs')
t = rep(t, "let quote=u64::try_from(amount as u128*curve.virtual_quote_reserves as u128/(curve.virtual_token_reserves as u128+amount as u128)).map_err(|_|error!(PumpError::Truncation))?;",
        "let quote=u64::try_from(curve.sell_quote(amount)?).map_err(|_|error!(PumpError::Truncation))?;", what='sell_v3 quote')
wr('trade_v3.rs', t)
t = rd('multi_hop_curve_swap.rs')
t = rep(t, "let gross_sell = u64::try_from(div(amount as u128 * c.virtual_quote_reserves as u128, c.virtual_token_reserves as u128 + amount as u128)?).map_err(|_| error!(PumpError::Truncation))?;",
        "let gross_sell = u64::try_from(c.sell_quote(amount)?).map_err(|_| error!(PumpError::Truncation))?;", what='multi-hop sell quote')
wr('multi_hop_curve_swap.rs', t)
f = 'creator/migrate_bonding_curve_creator.rs'
t = rd(f)
t = rep(t, " let a=&mut ctx.accounts;require!(!a.bonding_curve.is_holder_reward,PumpError::HolderRewardCreatorImmutable);require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);\n",
        " let a=&mut ctx.accounts;\n require!(!a.bonding_curve.is_holder_reward,PumpError::HolderRewardCreatorImmutable);\n require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);\n",
        what='migrate_bonding_curve_creator requires')
wr(f, t)
t = rd('trade_types.rs')
t = rep(t, "pub use crate::pump_fees::{\n    accounts::FeeConfig,\n    types::{FeeTier, Fees, Shareholder},\n};\n",
        "pub use crate::pump_fees::{\n\n    types::{FeeTier, Fees, Shareholder},\n};\n", what='FeeConfig alias')
t = t.rstrip('\n') + '\n' + """
// Route decoding has its own Rust type; the external CPI account keeps the IDL type.
#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct FeeConfig {
    pub bump: u8,
    pub admin: Pubkey,
    pub flat_fees: Fees,
    pub fee_tiers: Vec<FeeTier>,
    pub stable_fee_tiers: Vec<FeeTier>,
    pub exotic_flat_fees: Fees,
}
"""
wr('trade_types.rs', t)
print('integ_genuine applied (sell_quote callers, creator-migration require lines, route FeeConfig type)')
