//! Captured accounting of Pump `buy_v2` and `buy_exact_quote_in_v2` on the
//! native (WSOL quote mint) path of a regular coin (not Mayhem, cashback,
//! holder-reward, or the whitelist PDA user).
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured Pump
//! Fees program by `tests/test_buy_v2_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim. Pricing, fees, rent top-up,
//! buyback split, and reserve updates are the legacy ones; this module reuses
//! `legacy_buy.rs` (and through it `constant_product.rs`), which the host
//! declares beside this module.

use crate::legacy_buy::{self, Config, Fill, Stop};

pub use crate::legacy_buy::Curve;

pub const NOT_AUTHORIZED: u32 = 6000;
pub const BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED: u32 = 6057;

/// The named recipients the v2 buys take instead of legacy remaining accounts.
pub struct Recipients {
    /// `fee_recipient` is `global.fee_recipient` (its quote ATA matching).
    pub fee_recipient_ok: bool,
    /// `buyback_fee_recipient` is `global`'s buyback recipient (its quote ATA
    /// matching).
    pub buyback_ok: bool,
}

/// The single trailing `partial_fill` option bool. Unlike legacy, there is no
/// `track_volume` byte: a missing byte is `false`, a byte other than 0 or 1
/// fails to deserialize (102), and extra bytes are ignored.
pub fn parse_partial(trailing: &[u8]) -> Result<bool, Stop> {
    match trailing.first() {
        None | Some(0) => Ok(false),
        Some(1) => Ok(true),
        Some(_) => Err(Stop::Code(legacy_buy::INSTRUCTION_DID_NOT_DESERIALIZE)),
    }
}

/// Recipient checks: the fee recipient first, then the buyback recipient.
fn check_recipients(recipients: &Recipients) -> Result<(), Stop> {
    if !recipients.fee_recipient_ok {
        return Err(Stop::Code(NOT_AUTHORIZED));
    }
    if !recipients.buyback_ok {
        return Err(Stop::Code(BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED));
    }
    Ok(())
}

/// `buy_v2(amount, max_sol_cost, partial_fill)`: the legacy entry guards
/// (complete 6005, partial clamp, zero 6020, short reserves 6021), then the
/// recipient checks, then legacy pricing, fees, and the 6002 bound. The
/// emitted TradeEvent has `track_volume = false` and `ix_name = "buy"`.
pub fn buy_v2(
    curve: &Curve,
    config: &Config,
    recipients: &Recipients,
    amount: u64,
    max_sol_cost: u64,
    trailing: &[u8],
) -> Result<Fill, Stop> {
    let partial = parse_partial(trailing)?;
    if curve.complete {
        return Err(Stop::Code(legacy_buy::BONDING_CURVE_COMPLETE));
    }
    let clamped = if partial { amount.min(curve.real_token_reserves) } else { amount };
    if clamped == 0 {
        return Err(Stop::Code(legacy_buy::BUY_ZERO_AMOUNT));
    }
    if curve.real_token_reserves < clamped {
        return Err(Stop::Code(legacy_buy::NOT_ENOUGH_TOKENS_TO_BUY));
    }
    check_recipients(recipients)?;
    legacy_buy::buy(curve, config, amount, max_sol_cost, &[0, partial as u8])
}

/// `buy_exact_quote_in_v2(spendable_quote_in, min_tokens_out, partial_fill)`:
/// the legacy entry guards (complete 6005, zero minimum 6020, zero spend
/// 6041), then the recipient checks, then legacy `buy_exact_sol_in` pricing,
/// including the untouched fees on a trimmed quote and the partial-fill
/// re-quote. The emitted TradeEvent has `track_volume = false` and
/// `ix_name = "buy_exact_quote_in"`.
pub fn buy_exact_quote_in_v2(
    curve: &Curve,
    config: &Config,
    recipients: &Recipients,
    spendable: u64,
    min_tokens_out: u64,
    trailing: &[u8],
) -> Result<Fill, Stop> {
    let partial = parse_partial(trailing)?;
    if curve.complete {
        return Err(Stop::Code(legacy_buy::BONDING_CURVE_COMPLETE));
    }
    if min_tokens_out == 0 {
        return Err(Stop::Code(legacy_buy::BUY_ZERO_AMOUNT));
    }
    if spendable == 0 {
        return Err(Stop::Code(legacy_buy::NOT_ENOUGH_SOL_TO_COVER_FEES));
    }
    check_recipients(recipients)?;
    legacy_buy::buy_exact_sol_in(curve, config, spendable, min_tokens_out, &[0, partial as u8])
}
