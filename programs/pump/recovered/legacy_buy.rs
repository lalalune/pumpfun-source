//! Captured accounting of Pump legacy `buy` and `buy_exact_sol_in` on the SOL
//! path of a regular coin (not Mayhem, cashback, holder-reward, or the
//! whitelist PDA user).
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured Pump
//! Fees program by `tests/test_legacy_buy_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim. The curve quotient reuses
//! `constant_product.rs`, which the host declares beside this module.

use crate::constant_product::constant_product_output;

pub const TOO_MUCH_SOL_REQUIRED: u32 = 6002;
pub const BONDING_CURVE_COMPLETE: u32 = 6005;
pub const BUY_ZERO_AMOUNT: u32 = 6020;
pub const NOT_ENOUGH_TOKENS_TO_BUY: u32 = 6021;
pub const OVERFLOW: u32 = 6024;
pub const TRUNCATION: u32 = 6025;
pub const DIVISION_BY_ZERO: u32 = 6026;
pub const NOT_ENOUGH_SOL_TO_COVER_FEES: u32 = 6041;
pub const SLIPPAGE_BELOW_MIN_TOKENS_OUT: u32 = 6042;
pub const INSTRUCTION_DID_NOT_DESERIALIZE: u32 = 102;
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

pub struct Config<'a> {
    pub tiers: &'a [Tier],
    pub mint_supply: u64,
    pub creator_fee_configurable: bool,
    pub buyback_bps: u64,
    pub vault_lamports: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Fill {
    pub tokens: u64,
    pub sol_cost: u64,
    pub protocol_bps: u64,
    pub protocol_fee: u64,
    pub creator_bps: u64,
    pub creator_fee: u64,
    pub buyback_fee: u64,
    /// Lamports the creator vault receives, including any rent top-up.
    pub vault_credit: u64,
    pub curve: Curve,
}

/// Trailing `track_volume` and `partial_fill` option bools. A missing byte is
/// `false`; a byte other than 0 or 1 fails to deserialize; extra bytes are ignored.
pub fn parse_options(trailing: &[u8]) -> Result<(bool, bool), Stop> {
    let mut flags = [false; 2];
    for (slot, byte) in flags.iter_mut().zip(trailing.iter()) {
        *slot = match byte {
            0 => false,
            1 => true,
            _ => return Err(Stop::Code(INSTRUCTION_DID_NOT_DESERIALIZE)),
        };
    }
    Ok((flags[0], flags[1]))
}

/// Market cap passed to Pump Fees: `mint.supply * virtual_sol / virtual_token`.
fn market_cap(curve: &Curve, supply: u64) -> Result<u128, Stop> {
    (supply as u128 * curve.virtual_sol_reserves as u128)
        .checked_div(curve.virtual_token_reserves as u128)
        .ok_or(Stop::Code(DIVISION_BY_ZERO))
}

/// Pump Fees tier choice. The first tier wins below its own threshold; otherwise
/// the last tier at or below the market cap. An empty list aborts.
fn select_tier(tiers: &[Tier], market_cap: u128) -> Result<(u64, u64), Stop> {
    let first = tiers.first().ok_or(Stop::Panic)?;
    if market_cap < first.threshold {
        return Ok((first.protocol_bps, first.creator_bps));
    }
    let tier = tiers.iter().rev().find(|t| market_cap >= t.threshold).unwrap_or(first);
    Ok((tier.protocol_bps, tier.creator_bps))
}

/// Protocol and creator bps after the configurable creator override. The
/// shared fee helper also prices `quote` at those rates, so a fee that leaves
/// u64 fails here (6025) even when the caller later uses a smaller quote.
fn fee_bps(curve: &Curve, config: &Config, quote: u64) -> Result<(u64, u64), Stop> {
    let (protocol, creator) = select_tier(config.tiers, market_cap(curve, config.mint_supply)?)?;
    let creator = if config.creator_fee_configurable && curve.creator_fee_bps != 0 {
        curve.creator_fee_bps
    } else {
        creator
    };
    ceil_fee(quote, protocol)?;
    if curve.has_creator {
        ceil_fee(quote, creator)?;
    }
    Ok((protocol, creator))
}

/// Ceiling fee: `ceil(amount * bps / 10000)`, 6025 when it leaves u64.
fn ceil_fee(amount: u64, bps: u64) -> Result<u64, Stop> {
    let value = (amount as u128 * bps as u128 + 9999) / 10000;
    u64::try_from(value).map_err(|_| Stop::Code(TRUNCATION))
}

/// Normal buy quote: `amount * virtual_sol / (virtual_token - amount) + 1`.
fn buy_quote(curve: &Curve, amount: u64) -> Result<u64, Stop> {
    let denominator = (curve.virtual_token_reserves as u128)
        .checked_sub(amount as u128)
        .ok_or(Stop::Code(OVERFLOW))?;
    if denominator == 0 {
        return Err(Stop::Code(DIVISION_BY_ZERO));
    }
    let quote = amount as u128 * curve.virtual_sol_reserves as u128 / denominator + 1;
    u64::try_from(quote).map_err(|_| Stop::Code(TRUNCATION))
}

fn settle(
    curve: &Curve,
    config: &Config,
    tokens: u64,
    sol_cost: u64,
    bps: (u64, u64),
    protocol_fee: u64,
    creator_fee: u64,
) -> Result<Fill, Stop> {
    let mut next = *curve;
    next.virtual_token_reserves = next.virtual_token_reserves.checked_sub(tokens).ok_or(Stop::Code(OVERFLOW))?;
    next.real_token_reserves = next.real_token_reserves.checked_sub(tokens).ok_or(Stop::Code(OVERFLOW))?;
    next.virtual_sol_reserves = next.virtual_sol_reserves.checked_add(sol_cost).ok_or(Stop::Code(OVERFLOW))?;
    next.real_sol_reserves = next.real_sol_reserves.checked_add(sol_cost).ok_or(Stop::Code(OVERFLOW))?;
    next.complete = next.real_token_reserves == 0;
    // A vault below the zero-byte minimum is topped up by the whole minimum,
    // not by the shortfall, before the creator fee is paid.
    let vault_credit = if creator_fee == 0 {
        0
    } else if config.vault_lamports < VAULT_RENT_MINIMUM {
        VAULT_RENT_MINIMUM + creator_fee
    } else {
        creator_fee
    };
    let buyback_fee = (config.buyback_bps as u128 * protocol_fee as u128 / 10000) as u64;
    if buyback_fee > protocol_fee {
        return Err(Stop::Panic);
    }
    Ok(Fill {
        tokens,
        sol_cost,
        protocol_bps: bps.0,
        protocol_fee,
        creator_bps: bps.1,
        creator_fee,
        buyback_fee,
        vault_credit,
        curve: next,
    })
}

/// Legacy `buy(amount, max_sol_cost, track_volume, partial_fill)`.
pub fn buy(curve: &Curve, config: &Config, amount: u64, max_sol_cost: u64, trailing: &[u8]) -> Result<Fill, Stop> {
    let (_, partial) = parse_options(trailing)?;
    if curve.complete {
        return Err(Stop::Code(BONDING_CURVE_COMPLETE));
    }
    let amount = if partial { amount.min(curve.real_token_reserves) } else { amount };
    if amount == 0 {
        return Err(Stop::Code(BUY_ZERO_AMOUNT));
    }
    if curve.real_token_reserves < amount {
        return Err(Stop::Code(NOT_ENOUGH_TOKENS_TO_BUY));
    }
    let sol_cost = buy_quote(curve, amount)?;
    let bps = fee_bps(curve, config, sol_cost)?;
    let protocol_fee = ceil_fee(sol_cost, bps.0)?;
    let creator_fee = if curve.has_creator { ceil_fee(sol_cost, bps.1)? } else { 0 };
    let total = sol_cost
        .checked_add(protocol_fee)
        .and_then(|v| v.checked_add(creator_fee))
        .ok_or(Stop::Code(OVERFLOW))?;
    if max_sol_cost < total {
        return Err(Stop::Code(TOO_MUCH_SOL_REQUIRED));
    }
    settle(curve, config, amount, sol_cost, bps, protocol_fee, creator_fee)
}

/// Legacy `buy_exact_sol_in(spendable_sol_in, min_tokens_out, track_volume, partial_fill)`.
pub fn buy_exact_sol_in(
    curve: &Curve,
    config: &Config,
    spendable: u64,
    min_tokens_out: u64,
    trailing: &[u8],
) -> Result<Fill, Stop> {
    let (_, partial) = parse_options(trailing)?;
    if curve.complete {
        return Err(Stop::Code(BONDING_CURVE_COMPLETE));
    }
    if min_tokens_out == 0 {
        return Err(Stop::Code(BUY_ZERO_AMOUNT));
    }
    if spendable == 0 {
        return Err(Stop::Code(NOT_ENOUGH_SOL_TO_COVER_FEES));
    }
    let bps = fee_bps(curve, config, spendable)?;
    let creator_bps = if curve.has_creator { bps.1 } else { 0 };
    let total_bps = bps.0.checked_add(creator_bps).ok_or(Stop::Code(OVERFLOW))?;
    let raw = if total_bps == 0 {
        spendable
    } else {
        (spendable as u128 * 10000 / (10000 + total_bps as u128)) as u64
    };
    if raw == 0 {
        return Err(Stop::Code(NOT_ENOUGH_SOL_TO_COVER_FEES));
    }
    // Fees are taken on the pre-adjustment quote and are not recomputed when
    // the quote is trimmed to fit the spendable amount.
    let protocol_fee = ceil_fee(raw, bps.0)?;
    let creator_fee = if curve.has_creator { ceil_fee(raw, bps.1)? } else { 0 };
    let total = raw.saturating_add(protocol_fee).saturating_add(creator_fee);
    let mut quote = raw;
    if total > spendable {
        quote = raw.checked_sub(total - spendable).ok_or(Stop::Code(OVERFLOW))?;
        if quote == 0 {
            return Err(Stop::Code(SLIPPAGE_BELOW_MIN_TOKENS_OUT));
        }
    }
    let out = constant_product_output(
        (quote - 1) as u128,
        curve.virtual_sol_reserves as u128,
        curve.virtual_token_reserves as u128,
    )
    .map_err(|e| Stop::Code(e as u32))?;
    let tokens = u64::try_from(out).map_err(|_| Stop::Code(TRUNCATION))?;
    let (tokens, quote, protocol_fee, creator_fee) = if tokens > curve.real_token_reserves && partial {
        let tokens = curve.real_token_reserves;
        let quote = buy_quote(curve, tokens)?;
        let protocol_fee = ceil_fee(quote, bps.0)?;
        let creator_fee = if curve.has_creator { ceil_fee(quote, bps.1)? } else { 0 };
        let total = quote
            .checked_add(protocol_fee)
            .and_then(|v| v.checked_add(creator_fee))
            .ok_or(Stop::Code(OVERFLOW))?;
        if spendable < total {
            return Err(Stop::Code(TOO_MUCH_SOL_REQUIRED));
        }
        (tokens, quote, protocol_fee, creator_fee)
    } else {
        if tokens < min_tokens_out {
            return Err(Stop::Code(SLIPPAGE_BELOW_MIN_TOKENS_OUT));
        }
        (tokens, quote, protocol_fee, creator_fee)
    };
    if curve.real_token_reserves < tokens {
        return Err(Stop::Code(NOT_ENOUGH_TOKENS_TO_BUY));
    }
    settle(curve, config, tokens, quote, bps, protocol_fee, creator_fee)
}
