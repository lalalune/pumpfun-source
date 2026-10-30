//! Captured accounting of Pump legacy `sell` on the SOL path of a regular
//! coin (not Mayhem, cashback, holder-reward, or the whitelist PDA user).
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured Pump
//! Fees program by `tests/test_legacy_sell_captured.py`. Not linked into the
//! SBF crate. This is not a byte-identity claim.

pub const TOO_LITTLE_SOL_RECEIVED: u32 = 6003;
pub const BONDING_CURVE_COMPLETE: u32 = 6005;
pub const SELL_ZERO_AMOUNT: u32 = 6022;
pub const NOT_ENOUGH_TOKENS_TO_SELL: u32 = 6023;
pub const OVERFLOW: u32 = 6024;
pub const TRUNCATION: u32 = 6025;
pub const DIVISION_BY_ZERO: u32 = 6026;
pub const BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED: u32 = 6057;
pub const BUYBACK_FEE_RECIPIENT_MISSING: u32 = 6062;
pub const INVALID_BONDING_CURVE_V2: u32 = 6074;
/// `Rent::minimum_balance(0)` under default rent.
pub const VAULT_RENT_MINIMUM: u64 = 890_880;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    /// The program aborts without an Anchor error (`ProgramFailedToComplete`).
    Panic,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Curve {
    pub virtual_token_reserves: u64,
    pub virtual_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub real_sol_reserves: u64,
    pub complete: bool,
    pub has_creator: bool,
    pub creator_fee_bps: u64,
}

/// One `FeeConfig.fee_tiers` entry: threshold, protocol bps, creator bps.
#[derive(Debug, Clone, Copy)]
pub struct Tier {
    pub threshold: u128,
    pub protocol_bps: u64,
    pub creator_bps: u64,
}

/// What the instruction's remaining accounts hold at index 0 and 1.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Slot {
    Absent,
    /// The `bonding-curve-v2` PDA of the mint.
    CurveV2,
    /// A key listed in `Global.buyback_fee_recipients`.
    Buyback,
    /// The all-zero key.
    Zero,
    /// Any other key.
    Other,
}

pub struct Config<'a> {
    pub tiers: &'a [Tier],
    pub mint_supply: u64,
    pub creator_fee_configurable: bool,
    pub buyback_bps: u64,
    pub vault_lamports: u64,
    pub user_tokens: u64,
    pub remaining: [Slot; 2],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Fill {
    pub sol_output: u64,
    pub protocol_bps: u64,
    pub protocol_fee: u64,
    pub creator_bps: u64,
    pub creator_fee: u64,
    pub buyback_fee: u64,
    /// Rent top-up the seller pays into the creator vault.
    pub vault_top_up: u64,
    /// Lamports the seller receives from the curve.
    pub user_output: u64,
    pub curve: Curve,
}

fn select_tier(tiers: &[Tier], market_cap: u128) -> Result<(u64, u64), Stop> {
    let first = tiers.first().ok_or(Stop::Panic)?;
    if market_cap < first.threshold {
        return Ok((first.protocol_bps, first.creator_bps));
    }
    let tier = tiers.iter().rev().find(|t| market_cap >= t.threshold).unwrap_or(first);
    Ok((tier.protocol_bps, tier.creator_bps))
}

fn ceil_fee(amount: u64, bps: u64) -> Result<u64, Stop> {
    u64::try_from((amount as u128 * bps as u128 + 9999) / 10000).map_err(|_| Stop::Code(TRUNCATION))
}

/// Shared fee helper: tier by pre-trade `mint.supply * vs / vt`, configurable
/// creator-bps override, ceiling fees on `quote` (creator fee only with a creator).
fn trade_fees(curve: &Curve, config: &Config, quote: u64) -> Result<(u64, u64, u64, u64), Stop> {
    let market_cap = (config.mint_supply as u128 * curve.virtual_sol_reserves as u128)
        .checked_div(curve.virtual_token_reserves as u128)
        .ok_or(Stop::Code(DIVISION_BY_ZERO))?;
    let (protocol_bps, tier_creator_bps) = select_tier(config.tiers, market_cap)?;
    let creator_bps = if config.creator_fee_configurable && curve.creator_fee_bps != 0 {
        curve.creator_fee_bps
    } else {
        tier_creator_bps
    };
    let protocol_fee = ceil_fee(quote, protocol_bps)?;
    let creator_fee = if curve.has_creator { ceil_fee(quote, creator_bps)? } else { 0 };
    Ok((protocol_fee, creator_fee, protocol_bps, creator_bps))
}

/// Legacy `sell(amount, min_sol_output)`.
pub fn sell(curve: &Curve, config: &Config, amount: u64, min_sol_output: u64) -> Result<Fill, Stop> {
    let overflow = Stop::Code(OVERFLOW);
    if curve.complete {
        return Err(Stop::Code(BONDING_CURVE_COMPLETE));
    }
    if amount == 0 {
        return Err(Stop::Code(SELL_ZERO_AMOUNT));
    }
    if config.user_tokens < amount {
        return Err(Stop::Code(NOT_ENOUGH_TOKENS_TO_SELL));
    }
    // floor(vs * amount / (vt + amount)); the u128 sum cannot be zero here.
    let sol_output = (curve.virtual_sol_reserves as u128 * amount as u128
        / (curve.virtual_token_reserves as u128 + amount as u128)) as u64;
    let (protocol_fee, creator_fee, protocol_bps, creator_bps) = trade_fees(curve, config, sol_output)?;
    let user_output = sol_output
        .checked_sub(protocol_fee)
        .and_then(|v| v.checked_sub(creator_fee))
        .ok_or(overflow)?;
    if user_output < min_sol_output {
        return Err(Stop::Code(TOO_LITTLE_SOL_RECEIVED));
    }
    let mut next = *curve;
    next.virtual_token_reserves = next.virtual_token_reserves.checked_add(amount).ok_or(overflow)?;
    next.real_token_reserves = next.real_token_reserves.checked_add(amount).ok_or(overflow)?;
    next.virtual_sol_reserves = next.virtual_sol_reserves.checked_sub(sol_output).ok_or(overflow)?;
    next.real_sol_reserves = next.real_sol_reserves.checked_sub(sol_output).ok_or(overflow)?;
    // The creator fee leaves the curve; a vault under the zero-byte minimum is
    // first topped up by the seller with the whole minimum.
    let mut vault_top_up = 0;
    if creator_fee != 0 {
        if config.remaining[0] != Slot::CurveV2 {
            return Err(Stop::Code(INVALID_BONDING_CURVE_V2));
        }
        if config.vault_lamports < VAULT_RENT_MINIMUM {
            vault_top_up = VAULT_RENT_MINIMUM;
        }
    }
    // The buyback recipient is required at index 1 even when no buyback is paid.
    match config.remaining[1] {
        Slot::Absent | Slot::Zero => return Err(Stop::Code(BUYBACK_FEE_RECIPIENT_MISSING)),
        Slot::Buyback => {}
        Slot::CurveV2 | Slot::Other => return Err(Stop::Code(BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED)),
    }
    let buyback_fee = (config.buyback_bps as u128 * protocol_fee as u128 / 10000) as u64;
    if buyback_fee > protocol_fee {
        return Err(Stop::Panic);
    }
    Ok(Fill {
        sol_output,
        protocol_bps,
        protocol_fee,
        creator_bps,
        creator_fee,
        buyback_fee,
        vault_top_up,
        user_output,
        curve: next,
    })
}
