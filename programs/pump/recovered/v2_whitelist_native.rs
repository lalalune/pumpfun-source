//! Captured accounting of Pump `sell_v2`, `buy_v2` and `buy_exact_quote_in_v2`
//! for the Global `whitelist_pda` user on a native SOL curve, which `sell_v2.rs`
//! and `buy_v2.rs` leave out: no fee CPI and no fees, and a trade on a mayhem
//! curve ends with the `mayhem_virtual_params.rs` resync at the SOL thresholds.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_v2_whitelist_native_captured.py`. Not linked into
//! the SBF crate. This is not a byte-identity claim.

use crate::mayhem_virtual_params as mayhem;

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

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Op {
    Sell,
    Buy,
    BuyExactQuoteIn,
}

#[derive(Clone, Copy, Debug)]
pub struct Case {
    pub op: Op,
    pub amount: u64,
    /// `min_sol_output`, `max_sol_cost` or `min_tokens_out`.
    pub limit: u64,
    pub partial_fill: bool,
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub token_total_supply: u64,
    pub complete: bool,
    pub mayhem: bool,
    pub user_base: u64,
    pub curve_base: u64,
    pub fee_recipient_ok: bool,
    pub buyback_ok: bool,
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

fn add(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_add(b).ok_or(OVERFLOW)
}
fn sub(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_sub(b).ok_or(OVERFLOW)
}

fn recipients(c: &Case) -> Result<(), u32> {
    if !c.fee_recipient_ok {
        return Err(NOT_AUTHORIZED);
    }
    if !c.buyback_ok {
        return Err(BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED);
    }
    Ok(())
}

/// The virtual quote reserve to store; the resync reads the settled curve, not
/// yet marked complete, and the curve's and the user's base balances.
fn resync(c: &Case, s: &Settled) -> Result<u64, u32> {
    let (curve_base, user_base) = if c.op == Op::Sell {
        (add(c.curve_base, s.base_moved)?, sub(c.user_base, s.base_moved)?)
    } else {
        (sub(c.curve_base, s.base_moved)?, add(c.user_base, s.base_moved)?)
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
    mayhem::sync(&curve, curve_base, user_base)
}

fn settle_buy(c: &Case, amount: u64, quote: u64) -> Result<Settled, u32> {
    if c.real_token_reserves < amount {
        return Err(NOT_ENOUGH_TOKENS_TO_BUY);
    }
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

fn buy_quote(c: &Case, amount: u64) -> Result<u64, u32> {
    let den = (c.virtual_token_reserves as u128).checked_sub(amount as u128).ok_or(OVERFLOW)?;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    u64::try_from(amount as u128 * c.virtual_quote_reserves as u128 / den + 1).map_err(|_| TRUNCATION)
}

fn sell(c: &Case) -> Result<Settled, u32> {
    if c.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    if c.amount == 0 {
        return Err(SELL_ZERO_AMOUNT);
    }
    if c.user_base < c.amount {
        return Err(NOT_ENOUGH_TOKENS_TO_SELL);
    }
    recipients(c)?;
    let den = c.virtual_token_reserves as u128 + c.amount as u128;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    let quote = u64::try_from(c.virtual_quote_reserves as u128 * c.amount as u128 / den).map_err(|_| TRUNCATION)?;
    if quote < c.limit {
        return Err(TOO_LITTLE_SOL_RECEIVED);
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

fn buy(c: &Case) -> Result<Settled, u32> {
    if c.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    let amount = if c.partial_fill { c.amount.min(c.real_token_reserves) } else { c.amount };
    if amount == 0 {
        return Err(BUY_ZERO_AMOUNT);
    }
    if c.real_token_reserves < amount {
        return Err(NOT_ENOUGH_TOKENS_TO_BUY);
    }
    recipients(c)?;
    let quote = buy_quote(c, amount)?;
    if c.limit < quote {
        return Err(TOO_MUCH_SOL_REQUIRED);
    }
    settle_buy(c, amount, quote)
}

fn buy_exact_quote_in(c: &Case) -> Result<Settled, u32> {
    if c.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    if c.limit == 0 {
        return Err(BUY_ZERO_AMOUNT);
    }
    if c.amount == 0 {
        return Err(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES);
    }
    recipients(c)?;
    let effective = (c.amount - 1) as u128;
    let den = c.virtual_quote_reserves as u128 + effective;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    let computed = u64::try_from(effective * c.virtual_token_reserves as u128 / den).map_err(|_| TRUNCATION)?;
    if computed > c.real_token_reserves && c.partial_fill {
        let amount = c.real_token_reserves;
        return settle_buy(c, amount, buy_quote(c, amount)?);
    }
    if computed < c.limit {
        return Err(BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT);
    }
    settle_buy(c, computed, c.amount)
}

pub fn run(c: &Case) -> Result<Settled, u32> {
    let mut s = match c.op {
        Op::Sell => sell(c),
        Op::Buy => buy(c),
        Op::BuyExactQuoteIn => buy_exact_quote_in(c),
    }?;
    s.virtual_quote_reserves = resync(c, &s)?;
    Ok(s)
}
