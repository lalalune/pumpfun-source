//! Quote accounting of Pump `sell_v3` and of `buy_v3` fills that stay on the
//! curve, for every quote kind the v3 handlers accept: native SOL, SPL Token
//! (flat fees, the wSOL / second-SOL-mint tiers, the USDC stable tiers) and
//! Token-2022 with or without a `TransferFeeConfig`.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_v3_trade_accounting_captured.py`. Buys that cross
//! into the post-complete pool are out of scope (`Outcome::Unmodelled`).
//! Account admission is assumed to pass; only value checks are modelled.

pub const BONDING_CURVE_COMPLETE: u32 = 6005;
pub const CASHBACK_COIN_NOT_SUPPORTED: u32 = 6094;
pub const TOO_MUCH_SOL_REQUIRED: u32 = 6002;
pub const TOO_LITTLE_SOL_RECEIVED: u32 = 6003;
pub const BUY_ZERO_AMOUNT: u32 = 6020;
pub const NOT_ENOUGH_TOKENS_TO_BUY: u32 = 6021;
pub const SELL_ZERO_AMOUNT: u32 = 6022;
pub const NOT_ENOUGH_TOKENS_TO_SELL: u32 = 6023;
pub const OVERFLOW: u32 = 6024;
pub const TRUNCATION: u32 = 6025;
pub const DIVISION_BY_ZERO: u32 = 6026;
pub const FEE_TIERS_EMPTY: u32 = 6096;
pub const FEE_CONFIG_TOO_SHORT: u32 = 6097;
/// SPL Token / Token-2022 `InsufficientFunds`.
pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;

pub const CURVE_LEN: u64 = 166;
pub fn rent(len: u64) -> u64 {
    (len + 128) * 6960
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum FeeTable {
    /// `fee_tiers`: native SOL, wSOL and the second SOL quote mint.
    Tiers,
    /// `stable_fee_tiers` (USDC), read only when the account is longer than 4,072 bytes.
    Stable,
    /// `flat_fees`, or `exotic_flat_fees` when the account is longer than 4,096 bytes and they are non-zero.
    Flat,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct Fee {
    pub epoch: u64,
    pub maximum_fee: u64,
    pub basis_points: u64,
}

impl Fee {
    pub fn calculate(&self, amount: u64) -> Option<u64> {
        if amount == 0 || self.basis_points == 0 {
            return Some(0);
        }
        let raw = (amount as u128 * self.basis_points as u128 + 9_999) / 10_000;
        Some((u64::try_from(raw).ok()?).min(self.maximum_fee))
    }
    pub fn pre_fee(&self, post: u64) -> Option<u64> {
        match (self.basis_points, post) {
            (0, _) => Some(post),
            (_, 0) => Some(0),
            (10_000, _) => self.maximum_fee.checked_add(post),
            (bps, _) => {
                let den = 10_000u128.checked_sub(bps as u128)?;
                let raw = (post as u128 * 10_000 + den - 1) / den;
                if raw - post as u128 >= self.maximum_fee as u128 {
                    post.checked_add(self.maximum_fee)
                } else {
                    u64::try_from(raw).ok()
                }
            }
        }
    }
}

#[derive(Clone, Copy, Default, Debug)]
pub struct TransferFee {
    pub older: Fee,
    pub newer: Fee,
}

#[derive(Clone, Debug)]
pub struct FeeConfig {
    pub len: u64,
    pub flat: (u64, u64),
    pub tiers: Vec<(u128, u64, u64)>,
    pub stable: Vec<(u128, u64, u64)>,
    pub exotic: (u64, u64, u64),
}

#[derive(Clone, Debug)]
pub struct Case {
    pub buy: bool,
    pub amount: u64,
    /// `min_sol_output` for a sell, `max_sol_cost` for a buy.
    pub limit: u64,
    pub partial_fill: bool,
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub token_total_supply: u64,
    pub complete: bool,
    pub cashback: bool,
    pub mayhem: bool,
    pub has_creator: bool,
    pub curve_creator_fee_bps: u64,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    pub curve_lamports: u64,
    pub native: bool,
    pub table: FeeTable,
    /// `TransferFeeConfig` of a Token-2022 quote mint; `None` for every other
    /// quote (the handlers never read it for native SOL or SPL Token mints).
    pub transfer_fee: Option<TransferFee>,
    pub epoch: u64,
    pub mint_supply: u64,
    pub buyback_bps: u64,
    pub creator_fee_configurable: bool,
    pub whitelisted_user: bool,
    pub fee_config: FeeConfig,
    pub user_base: u64,
    pub curve_base: u64,
    pub user_quote: u64,
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Settled {
    /// Signed quote deltas (lamports for native SOL, token units otherwise).
    pub user_quote: i128,
    pub curve_quote: i128,
    pub buyback_recipient: i128,
    /// Lamports the user tops the curve up with to keep 166 bytes rent-exempt
    /// (not included in `user_quote` / `curve_quote`).
    pub rent_top_up: u64,
    pub base_moved: u64,
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    // TradeEvent amounts
    pub quote: u64,
    pub protocol_fee_bps: u64,
    pub protocol_fee: u64,
    pub creator_fee_bps: u64,
    pub trade_creator_fee: u64,
    pub buyback_fee_bps: u64,
    pub event_buyback_fee: u64,
    pub quote_transfer_fee: u64,
    /// A buy that empties `real_token_reserves` sets `complete` and emits a
    /// `CompleteEvent` after the `TradeEvent`.
    pub completes: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    Ok(Settled),
    Error(u32),
    Unmodelled,
}

fn add(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_add(b).ok_or(OVERFLOW)
}
fn sub(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_sub(b).ok_or(OVERFLOW)
}

pub fn active_fee(c: &Case) -> Option<Fee> {
    c.transfer_fee.map(|t| if c.epoch >= t.newer.epoch { t.newer } else { t.older })
}
fn post_fee(fee: &Option<Fee>, amount: u64) -> Result<u64, u32> {
    match fee {
        None => Ok(amount),
        Some(f) => sub(amount, f.calculate(amount).ok_or(OVERFLOW)?),
    }
}
fn pre_fee(fee: &Option<Fee>, amount: u64) -> Result<u64, u32> {
    match fee {
        None => Ok(amount),
        Some(f) => f.pre_fee(amount).ok_or(OVERFLOW),
    }
}

fn tier(tiers: &[(u128, u64, u64)], market_cap: u128) -> Result<(u64, u64), u32> {
    let first = tiers.first().ok_or(FEE_TIERS_EMPTY)?;
    if market_cap < first.0 {
        return Ok((first.1, first.2));
    }
    let t = tiers.iter().rev().find(|t| market_cap >= t.0).unwrap_or(first);
    Ok((t.1, t.2))
}

fn bps(c: &Case, market_cap: u128) -> Result<(u64, u64), u32> {
    let f = &c.fee_config;
    if f.len < 2512 {
        return Err(FEE_CONFIG_TOO_SHORT);
    }
    match c.table {
        FeeTable::Tiers => tier(&f.tiers, market_cap),
        FeeTable::Stable => tier(if f.len > 4072 { &f.stable } else { &[] }, market_cap),
        FeeTable::Flat => {
            let e = f.exotic;
            if f.len > 4096 && (e.0 != 0 || e.1 != 0 || e.2 != 0) {
                Ok((e.1, e.2))
            } else {
                Ok(f.flat)
            }
        }
    }
}

fn fee(amount: u64, basis_points: u64) -> Result<u64, u32> {
    let v = (amount as u128 * basis_points as u128 + 9_999) / 10_000;
    u64::try_from(v).map_err(|_| TRUNCATION)
}

/// (protocol_fee, creator_fee, protocol_bps, creator_bps)
fn trade_fees(c: &Case, quote: u64) -> Result<(u64, u64, u64, u64), u32> {
    if c.whitelisted_user {
        return Ok((0, 0, 0, 0));
    }
    let supply = if c.mayhem { c.token_total_supply } else { c.mint_supply };
    if c.virtual_token_reserves == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    let market_cap = supply as u128 * c.virtual_quote_reserves as u128 / c.virtual_token_reserves as u128;
    let (protocol_bps, base_creator_bps) = bps(c, market_cap)?;
    let creator_bps = if c.creator_fee_configurable && c.curve_creator_fee_bps != 0 {
        c.curve_creator_fee_bps
    } else {
        base_creator_bps
    };
    let protocol = fee(quote, protocol_bps)?;
    let creator = if c.has_creator { fee(quote, creator_bps)? } else { 0 };
    Ok((protocol, creator, protocol_bps, creator_bps))
}

fn buyback_split(c: &Case, protocol_fee: u64) -> (u64, u64) {
    if c.mayhem {
        return (0, protocol_fee);
    }
    let b = (c.buyback_bps as u128 * protocol_fee as u128 / 10_000) as u64;
    (b, protocol_fee - b)
}

fn rent_top_up(c: &Case) -> Result<u64, u32> {
    let reserved = if c.native { add(c.real_quote_reserves, add(c.creator_fee, c.protocol_fees)?)? } else { 0 };
    let available = c.curve_lamports.saturating_sub(reserved);
    Ok(rent(CURVE_LEN).saturating_sub(available))
}

pub fn sell(c: &Case) -> Result<Settled, u32> {
    let top_up = rent_top_up(c)?;
    if c.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    if c.cashback {
        return Err(CASHBACK_COIN_NOT_SUPPORTED);
    }
    if c.amount == 0 {
        return Err(SELL_ZERO_AMOUNT);
    }
    if c.user_base < c.amount {
        return Err(NOT_ENOUGH_TOKENS_TO_SELL);
    }
    let tf = active_fee(c);
    let den = c.virtual_token_reserves as u128 + c.amount as u128;
    let quote = u64::try_from(c.virtual_quote_reserves as u128 * c.amount as u128 / den).map_err(|_| TRUNCATION)?;
    let (protocol_fee, creator_fee, protocol_bps, creator_bps) = trade_fees(c, quote)?;
    let user_output = sub(sub(quote, protocol_fee)?, creator_fee)?;
    let net_output = post_fee(&tf, user_output)?;
    if net_output < c.limit {
        return Err(TOO_LITTLE_SOL_RECEIVED);
    }
    let quote_transfer_fee = sub(user_output, net_output)?;
    let vtr = add(c.virtual_token_reserves, c.amount)?;
    let rtr = add(c.real_token_reserves, c.amount)?;
    let vqr = sub(c.virtual_quote_reserves, quote)?;
    let rqr = sub(c.real_quote_reserves, quote)?;
    let (buyback, retained) = buyback_split(c, protocol_fee);
    let protocol_fees = add(c.protocol_fees, retained)?;
    let creator_fees = add(c.creator_fee, creator_fee)?;
    let (user_q, buyback_q) = (post_fee(&tf, user_output)?, post_fee(&tf, buyback)?);
    Ok(Settled {
        user_quote: user_q as i128,
        curve_quote: -(user_output as i128) - buyback as i128,
        buyback_recipient: buyback_q as i128,
        rent_top_up: top_up,
        base_moved: c.amount,
        virtual_token_reserves: vtr,
        virtual_quote_reserves: vqr,
        real_token_reserves: rtr,
        real_quote_reserves: rqr,
        creator_fee: creator_fees,
        protocol_fees,
        quote,
        protocol_fee_bps: protocol_bps,
        protocol_fee,
        creator_fee_bps: creator_bps,
        trade_creator_fee: creator_fee,
        buyback_fee_bps: if c.mayhem { 0 } else { c.buyback_bps },
        event_buyback_fee: buyback_q,
        quote_transfer_fee,
        completes: false,
    })
}

pub fn buy(c: &Case) -> Outcome {
    let real = c.real_token_reserves;
    let can_cross = !(c.mayhem || c.whitelisted_user);
    if c.amount > real && can_cross && !c.complete && !c.cashback {
        return Outcome::Unmodelled;
    }
    match buy_on_curve(c) {
        Ok(s) => Outcome::Ok(s),
        Err(e) => Outcome::Error(e),
    }
}

fn buy_on_curve(c: &Case) -> Result<Settled, u32> {
    let top_up = rent_top_up(c)?;
    if c.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    if c.cashback {
        return Err(CASHBACK_COIN_NOT_SUPPORTED);
    }
    let real = c.real_token_reserves;
    let amount = if c.partial_fill { c.amount.min(real) } else { c.amount };
    if amount == 0 {
        return Err(BUY_ZERO_AMOUNT);
    }
    if real < amount {
        return Err(NOT_ENOUGH_TOKENS_TO_BUY);
    }
    let tf = active_fee(c);
    let den = (c.virtual_token_reserves as u128).checked_sub(amount as u128).ok_or(OVERFLOW)?;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    let quote = u64::try_from(amount as u128 * c.virtual_quote_reserves as u128 / den + 1).map_err(|_| TRUNCATION)?;
    let (protocol_fee, creator_fee, protocol_bps, creator_bps) = trade_fees(c, quote)?;
    let (buyback, retained) = buyback_split(c, protocol_fee);
    let first = add(add(quote, protocol_fee)?, creator_fee)?;
    let net = sub(first, buyback)?;
    let pool_quote = pre_fee(&tf, net)?;
    let quote_transfer_fee = sub(pool_quote, net)?;
    let cost = add(pool_quote, buyback)?;
    if c.limit < cost {
        return Err(TOO_MUCH_SOL_REQUIRED);
    }
    let vtr = sub(c.virtual_token_reserves, amount)?;
    let rtr = sub(c.real_token_reserves, amount)?;
    let vqr = add(c.virtual_quote_reserves, quote)?;
    let rqr = add(c.real_quote_reserves, quote)?;
    if c.curve_base < amount {
        return Err(TOKEN_INSUFFICIENT_FUNDS);
    }
    let protocol_fees = add(c.protocol_fees, retained)?;
    let creator_fees = add(c.creator_fee, creator_fee)?;
    if !c.native && c.user_quote < cost {
        return Err(TOKEN_INSUFFICIENT_FUNDS);
    }
    let curve_in = if c.native { cost as i128 - buyback as i128 } else { post_fee(&tf, pool_quote)? as i128 };
    let recipient_in = post_fee(&tf, buyback)?;
    Ok(Settled {
        user_quote: -(cost as i128),
        curve_quote: curve_in,
        buyback_recipient: recipient_in as i128,
        rent_top_up: top_up,
        base_moved: amount,
        virtual_token_reserves: vtr,
        virtual_quote_reserves: vqr,
        real_token_reserves: rtr,
        real_quote_reserves: rqr,
        creator_fee: creator_fees,
        protocol_fees,
        quote,
        protocol_fee_bps: protocol_bps,
        protocol_fee,
        creator_fee_bps: creator_bps,
        trade_creator_fee: creator_fee,
        buyback_fee_bps: if c.mayhem { 0 } else { c.buyback_bps },
        event_buyback_fee: recipient_in,
        quote_transfer_fee,
        completes: rtr == 0,
    })
}

pub fn run(c: &Case) -> Outcome {
    if c.buy {
        buy(c)
    } else {
        match sell(c) {
            Ok(s) => Outcome::Ok(s),
            Err(e) => Outcome::Error(e),
        }
    }
}
