//! Captured accounting of Pump `sell_v2` on the SOL path of a regular coin
//! (native curve, wrapped-SOL quote mint; not Mayhem, cashback or
//! holder-reward), expressed on top of the recovered legacy `sell` in
//! `legacy_sell.rs`.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured Pump
//! Fees program by `tests/test_sell_v2_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.

use crate::legacy_sell::{self, Config, Curve, Fill, Slot, Stop};

pub const NOT_AUTHORIZED: u32 = 6000;
pub const BONDING_CURVE_COMPLETE: u32 = legacy_sell::BONDING_CURVE_COMPLETE;
pub const SELL_ZERO_AMOUNT: u32 = legacy_sell::SELL_ZERO_AMOUNT;
pub const NOT_ENOUGH_TOKENS_TO_SELL: u32 = legacy_sell::NOT_ENOUGH_TOKENS_TO_SELL;
pub const BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED: u32 = legacy_sell::BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED;
/// Rent the seller pays to create its `user_volume_accumulator` (137 bytes)
/// when it does not exist yet.
pub const USER_VOLUME_ACCUMULATOR_RENT: u64 = 1_844_400;

/// The named recipients `sell_v2` takes instead of legacy remaining accounts.
pub struct Recipients {
    /// `fee_recipient` is `global.fee_recipient` (its quote ATA matching).
    pub fee_recipient_ok: bool,
    /// `buyback_fee_recipient` is in `global.buyback_fee_recipients` (its quote
    /// ATA matching).
    pub buyback_ok: bool,
}

/// `sell_v2(amount, min_sol_output)`: the legacy entry guards, then the
/// recipient checks (before any pricing, unlike legacy `sell`, where the
/// buyback slot is checked after the slippage bound), then legacy pricing,
/// fees, slippage and reserve updates unchanged. No `bonding-curve-v2`
/// account is required. Returns the fill and the accumulator rent.
pub fn sell_v2(
    curve: &Curve,
    config: &Config,
    recipients: &Recipients,
    amount: u64,
    min_sol_output: u64,
) -> Result<(Fill, u64), Stop> {
    if curve.complete {
        return Err(Stop::Code(BONDING_CURVE_COMPLETE));
    }
    if amount == 0 {
        return Err(Stop::Code(SELL_ZERO_AMOUNT));
    }
    if config.user_tokens < amount {
        return Err(Stop::Code(NOT_ENOUGH_TOKENS_TO_SELL));
    }
    if !recipients.fee_recipient_ok {
        return Err(Stop::Code(NOT_AUTHORIZED));
    }
    if !recipients.buyback_ok {
        return Err(Stop::Code(BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED));
    }
    let legacy = Config { remaining: [Slot::CurveV2, Slot::Buyback], ..*config };
    let fill = legacy_sell::sell(curve, &legacy, amount, min_sol_output)?;
    Ok((fill, USER_VOLUME_ACCUMULATOR_RENT))
}
