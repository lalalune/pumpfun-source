//! Captured accounting of Pump legacy `buy`, `buy_exact_sol_in` and `sell` for
//! the Global `whitelist_pda` user, which `legacy_buy.rs` and `legacy_sell.rs`
//! leave out. Unlike `v2_whitelist_native.rs`, the fee CPI still runs: its
//! result is thrown away, but a failure in it stops the trade. The creator fee
//! is zero, so the `bonding-curve-v2` slot at index 0 is never read.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_legacy_whitelist_captured.py`. Not linked into the
//! SBF crate. This is not a byte-identity claim.

use crate::mayhem_virtual_params as mayhem;

/// SPL Token `InsufficientFunds`.
pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;
pub const NOT_AUTHORIZED: u32 = 6000;
pub const TOO_MUCH_SOL_REQUIRED: u32 = 6002;
pub const TOO_LITTLE_SOL_RECEIVED: u32 = 6003;
pub const BONDING_CURVE_COMPLETE: u32 = 6005;
pub const BUY_ZERO_AMOUNT: u32 = 6020;
pub const NOT_ENOUGH_TOKENS_TO_BUY: u32 = 6021;
pub const SELL_ZERO_AMOUNT: u32 = 6022;
pub const NOT_ENOUGH_TOKENS_TO_SELL: u32 = 6023;
pub const OVERFLOW: u32 = 6024;
pub const TRUNCATION: u32 = 6025;
pub const DIVISION_BY_ZERO: u32 = 6026;
pub const BUY_NOT_ENOUGH_SOL_TO_COVER_FEES: u32 = 6041;
pub const BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT: u32 = 6042;
pub const BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED: u32 = 6057;
pub const BUYBACK_FEE_RECIPIENT_MISSING: u32 = 6062;
pub const INSTRUCTION_DID_NOT_DESERIALIZE: u32 = 102;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    /// The program aborts without an Anchor error (`ProgramFailedToComplete`).
    Panic,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Op {
    Sell,
    Buy,
    BuyExactSolIn,
}

/// What the instruction's remaining accounts hold at index 1.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Slot {
    Absent,
    /// A key listed in `Global.buyback_fee_recipients`.
    Buyback,
    /// The all-zero key.
    Zero,
    /// Any other key.
    Other,
}

/// One `FeeConfig.fee_tiers` entry: threshold, protocol bps, creator bps.
#[derive(Clone, Copy, Debug)]
pub struct Tier {
    pub threshold: u128,
    pub protocol_bps: u64,
    pub creator_bps: u64,
}

#[derive(Clone, Debug)]
pub struct Case {
    pub op: Op,
    pub amount: u64,
    /// `min_sol_output`, `max_sol_cost` or `min_tokens_out`.
    pub limit: u64,
    /// Instruction bytes after the two u64 arguments.
    pub trailing: Vec<u8>,
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub token_total_supply: u64,
    pub complete: bool,
    pub mayhem: bool,
    pub has_creator: bool,
    pub curve_creator_bps: u64,
    pub creator_fee_configurable: bool,
    pub mint_supply: u64,
    pub tiers: Vec<Tier>,
    pub user_base: u64,
    pub curve_base: u64,
    pub fee_recipient_ok: bool,
    pub slot1: Slot,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Settled {
    pub base_moved: u64,
    pub quote: u64,
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub completes: bool,
}

fn add(a: u64, b: u64) -> Result<u64, Stop> {
    a.checked_add(b).ok_or(Stop::Code(OVERFLOW))
}
fn sub(a: u64, b: u64) -> Result<u64, Stop> {
    a.checked_sub(b).ok_or(Stop::Code(OVERFLOW))
}

/// The fee quote is priced for its failures only: the whitelisted user pays no
/// fee, but a zero `virtual_token_reserves`, an empty tier list or a fee that
/// leaves u64 still stops the trade. A Mayhem curve prices its market cap on the
/// curve's `token_total_supply` instead of the mint supply.
fn fee_gate(c: &Case, quote: u64) -> Result<(), Stop> {
    let supply = if c.mayhem { c.token_total_supply } else { c.mint_supply };
    let market_cap = (supply as u128 * c.virtual_quote_reserves as u128)
        .checked_div(c.virtual_token_reserves as u128)
        .ok_or(Stop::Code(DIVISION_BY_ZERO))?;
    let first = c.tiers.first().ok_or(Stop::Panic)?;
    let tier = if market_cap < first.threshold {
        first
    } else {
        c.tiers.iter().rev().find(|t| market_cap >= t.threshold).unwrap_or(first)
    };
    let creator_bps = if c.creator_fee_configurable && c.curve_creator_bps != 0 {
        c.curve_creator_bps
    } else {
        tier.creator_bps
    };
    let ceil = |bps: u64| u64::try_from((quote as u128 * bps as u128 + 9999) / 10000).map_err(|_| Stop::Code(TRUNCATION));
    ceil(tier.protocol_bps)?;
    if c.has_creator {
        ceil(creator_bps)?;
    }
    Ok(())
}

/// The virtual quote reserve to store; the resync reads the settled curve, not
/// yet marked complete, and the curve's and the user's base balances after the
/// token transfer, which fails on a short curve balance and wraps on the receiver.
fn resync(c: &Case, s: &Settled) -> Result<u64, Stop> {
    let (curve_base, user_base) = if c.op == Op::Sell {
        (c.curve_base.wrapping_add(s.base_moved), c.user_base - s.base_moved)
    } else {
        if c.curve_base < s.base_moved {
            return Err(Stop::Code(TOKEN_INSUFFICIENT_FUNDS));
        }
        (c.curve_base - s.base_moved, c.user_base.wrapping_add(s.base_moved))
    };
    let curve = mayhem::Curve {
        virtual_token_reserves: s.virtual_token_reserves,
        virtual_quote_reserves: s.virtual_quote_reserves,
        real_token_reserves: s.real_token_reserves,
        real_quote_reserves: s.real_quote_reserves,
        token_total_supply: c.token_total_supply,
        complete: false,
        is_mayhem_mode: c.mayhem,
        native_quote: true,
    };
    mayhem::sync(&curve, curve_base, user_base).map_err(Stop::Code)
}

fn buy_quote(c: &Case, amount: u64) -> Result<u64, Stop> {
    let den = (c.virtual_token_reserves as u128).checked_sub(amount as u128).ok_or(Stop::Code(OVERFLOW))?;
    if den == 0 {
        return Err(Stop::Code(DIVISION_BY_ZERO));
    }
    u64::try_from(amount as u128 * c.virtual_quote_reserves as u128 / den + 1).map_err(|_| Stop::Code(TRUNCATION))
}

fn settle_buy(c: &Case, amount: u64, quote: u64) -> Result<Settled, Stop> {
    let real_token_reserves = sub(c.real_token_reserves, amount)?;
    Ok(Settled {
        base_moved: amount,
        quote,
        virtual_token_reserves: sub(c.virtual_token_reserves, amount)?,
        virtual_quote_reserves: add(c.virtual_quote_reserves, quote)?,
        real_token_reserves,
        real_quote_reserves: add(c.real_quote_reserves, quote)?,
        completes: real_token_reserves == 0,
    })
}

fn sell(c: &Case) -> Result<Settled, Stop> {
    if c.complete {
        return Err(Stop::Code(BONDING_CURVE_COMPLETE));
    }
    if c.amount == 0 {
        return Err(Stop::Code(SELL_ZERO_AMOUNT));
    }
    if c.user_base < c.amount {
        return Err(Stop::Code(NOT_ENOUGH_TOKENS_TO_SELL));
    }
    let den = c.virtual_token_reserves as u128 + c.amount as u128;
    let quote = (c.virtual_quote_reserves as u128 * c.amount as u128 / den) as u64;
    fee_gate(c, quote)?;
    if quote < c.limit {
        return Err(Stop::Code(TOO_LITTLE_SOL_RECEIVED));
    }
    Ok(Settled {
        base_moved: c.amount,
        quote,
        virtual_token_reserves: add(c.virtual_token_reserves, c.amount)?,
        virtual_quote_reserves: sub(c.virtual_quote_reserves, quote)?,
        real_token_reserves: add(c.real_token_reserves, c.amount)?,
        real_quote_reserves: sub(c.real_quote_reserves, quote)?,
        completes: false,
    })
}

fn buy(c: &Case, partial: bool) -> Result<Settled, Stop> {
    if c.complete {
        return Err(Stop::Code(BONDING_CURVE_COMPLETE));
    }
    let amount = if partial { c.amount.min(c.real_token_reserves) } else { c.amount };
    if amount == 0 {
        return Err(Stop::Code(BUY_ZERO_AMOUNT));
    }
    if c.real_token_reserves < amount {
        return Err(Stop::Code(NOT_ENOUGH_TOKENS_TO_BUY));
    }
    let quote = buy_quote(c, amount)?;
    fee_gate(c, quote)?;
    if c.limit < quote {
        return Err(Stop::Code(TOO_MUCH_SOL_REQUIRED));
    }
    settle_buy(c, amount, quote)
}

fn buy_exact_sol_in(c: &Case, partial: bool) -> Result<Settled, Stop> {
    if c.complete {
        return Err(Stop::Code(BONDING_CURVE_COMPLETE));
    }
    if c.limit == 0 {
        return Err(Stop::Code(BUY_ZERO_AMOUNT));
    }
    if c.amount == 0 {
        return Err(Stop::Code(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES));
    }
    fee_gate(c, c.amount)?;
    let effective = (c.amount - 1) as u128;
    let den = c.virtual_quote_reserves as u128 + effective;
    if den == 0 {
        return Err(Stop::Code(DIVISION_BY_ZERO));
    }
    let computed = u64::try_from(effective * c.virtual_token_reserves as u128 / den).map_err(|_| Stop::Code(TRUNCATION))?;
    if computed > c.real_token_reserves && partial {
        let amount = c.real_token_reserves;
        let quote = buy_quote(c, amount)?;
        // Unconfirmed: no input reached this; `computed` above the real reserve
        // already implies a smaller `quote`.
        if c.amount < quote {
            return Err(Stop::Code(TOO_MUCH_SOL_REQUIRED));
        }
        return settle_buy(c, amount, quote);
    }
    if computed < c.limit {
        return Err(Stop::Code(BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT));
    }
    if c.real_token_reserves < computed {
        return Err(Stop::Code(NOT_ENOUGH_TOKENS_TO_BUY));
    }
    settle_buy(c, computed, c.amount)
}

/// Trailing `track_volume` and `partial_fill` option bools of the two buys. A
/// missing byte is `false`; a byte other than 0 or 1 fails to deserialize.
fn partial_fill(trailing: &[u8]) -> Result<bool, Stop> {
    if trailing.iter().take(2).any(|byte| *byte > 1) {
        return Err(Stop::Code(INSTRUCTION_DID_NOT_DESERIALIZE));
    }
    Ok(trailing.get(1) == Some(&1))
}

/// The buyback recipient is required at index 1 even when no buyback is paid.
fn buyback_recipient(c: &Case) -> Result<(), Stop> {
    match c.slot1 {
        Slot::Absent | Slot::Zero => Err(Stop::Code(BUYBACK_FEE_RECIPIENT_MISSING)),
        Slot::Other => Err(Stop::Code(BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED)),
        Slot::Buyback => Ok(()),
    }
}

/// The instruction arguments decode first, then the fee recipient. The two buys
/// check the buyback recipient next, ahead of every curve guard; `sell` checks
/// it last, after the resync.
pub fn run(c: &Case) -> Result<Settled, Stop> {
    let partial = if c.op == Op::Sell { false } else { partial_fill(&c.trailing)? };
    if !c.fee_recipient_ok {
        return Err(Stop::Code(NOT_AUTHORIZED));
    }
    if c.op != Op::Sell {
        buyback_recipient(c)?;
    }
    let mut s = match c.op {
        Op::Sell => sell(c),
        Op::Buy => buy(c, partial),
        Op::BuyExactSolIn => buy_exact_sol_in(c, partial),
    }?;
    s.virtual_quote_reserves = resync(c, &s)?;
    if c.op == Op::Sell {
        buyback_recipient(c)?;
    }
    Ok(s)
}
