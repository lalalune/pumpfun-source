//! Captured rules of Pump `buy_exact_quote_in_v3`: spending a fixed quote
//! budget on a bonding curve, for every quote kind the v3 handlers accept, with
//! the on-curve path and the path that fills the curve and crosses into the
//! post-complete pool. Also `buy_v3` fills that cross, which
//! `v3_trade_accounting.rs` leaves as `Outcome::Unmodelled`.
//!
//! Shares the state, fee and result types of `v3_trade_accounting.rs`. For the
//! exact-quote buy `Case::amount` is `spendable_quote_in` and `Case::limit` is
//! `min_tokens_out`; for `buy_v3` they are `amount` and `max_sol_cost`.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_v3_exact_quote_captured.py`. Account admission is
//! assumed to pass; only value checks are modelled. A whitelisted user on a
//! mayhem curve resyncs the virtual reserves and is out of scope (`Err(None)`).
//!
//! Branches marked 미확인 (unconfirmed) are carried over from the program
//! sources: no captured run enters them, so their codes and arithmetic are not
//! pinned by this file. The net and fees are sized to `available`, and grossing
//! up never costs less than the buyback it leaves out, so the total stayed
//! within the budget on every captured input and these guards stayed idle.

use crate::v3_trade_accounting::*;

pub const BUY_NOT_ENOUGH_SOL_TO_COVER_FEES: u32 = 6041;
pub const BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT: u32 = 6042;

/// Global fields the v3 buys read beyond `Case`.
#[derive(Clone, Debug)]
pub struct ExactQuote {
    pub case: Case,
    pub pool_migration_fee: u64,
}

/// Post-complete fill; `buyback_fee` is the net amount of its PostCompleteBuyEvent.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Post {
    pub base_out: u64,
    pub quote_in: u64,
    pub protocol_fee: u64,
    pub creator_fee: u64,
    pub pool_base_before: u64,
    pub pool_quote_before: u64,
    pub buyback_fee: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Filled {
    pub settled: Settled,
    pub post: Option<Post>,
}

#[derive(Clone, Copy, Debug, Default)]
struct TradeFees {
    protocol: u64,
    creator: u64,
    protocol_bps: u64,
    creator_bps: u64,
}

/// (pool_quote, total_buyback, quote_transfer_fee)
type Costs = (u64, u64, u64);

fn add(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_add(b).ok_or(OVERFLOW)
}
fn sub(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_sub(b).ok_or(OVERFLOW)
}
fn add3(a: u64, b: u64, c: u64) -> Result<u64, u32> {
    add(add(a, b)?, c)
}

fn post_fee(tf: &Option<Fee>, amount: u64) -> Result<u64, u32> {
    match tf {
        None => Ok(amount),
        Some(f) => sub(amount, f.calculate(amount).ok_or(OVERFLOW)?),
    }
}
fn pre_fee(tf: &Option<Fee>, amount: u64) -> Result<u64, u32> {
    match tf {
        None => Ok(amount),
        Some(f) => f.pre_fee(amount).ok_or(OVERFLOW),
    }
}

fn fee(amount: u64, basis_points: u64) -> Result<u64, u32> {
    let v = (amount as u128 * basis_points as u128 + 9_999) / 10_000;
    u64::try_from(v).map_err(|_| TRUNCATION)
}

fn tier(tiers: &[(u128, u64, u64)], market_cap: u128) -> Result<(u64, u64), u32> {
    let first = tiers.first().ok_or(FEE_TIERS_EMPTY)?;
    if market_cap < first.0 {
        return Ok((first.1, first.2));
    }
    let t = tiers.iter().rev().find(|t| market_cap >= t.0).unwrap_or(first);
    Ok((t.1, t.2))
}

fn table_bps(c: &Case, market_cap: u128) -> Result<(u64, u64), u32> {
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

fn trade_fees(c: &Case, quote: u64) -> Result<TradeFees, u32> {
    if c.whitelisted_user {
        return Ok(TradeFees::default());
    }
    let supply = if c.mayhem { c.token_total_supply } else { c.mint_supply };
    if c.virtual_token_reserves == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    let market_cap = supply as u128 * c.virtual_quote_reserves as u128 / c.virtual_token_reserves as u128;
    let (protocol_bps, base_creator_bps) = table_bps(c, market_cap)?;
    let creator_bps = if c.creator_fee_configurable && c.curve_creator_fee_bps != 0 {
        c.curve_creator_fee_bps
    } else {
        base_creator_bps
    };
    let protocol = fee(quote, protocol_bps)?;
    let creator = if c.has_creator { fee(quote, creator_bps)? } else { 0 };
    Ok(TradeFees { protocol, creator, protocol_bps, creator_bps })
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

fn output(amount_in: u64, reserve_in: u64, reserve_out: u64) -> Result<u64, u32> {
    let numerator = amount_in as u128 * reserve_out as u128;
    let denominator = reserve_in as u128 + amount_in as u128;
    if denominator == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    u64::try_from(numerator / denominator).map_err(|_| TRUNCATION)
}

/// Tokens a net quote buys: one quote unit is kept back before pricing.
fn tokens_for_quote(c: &Case, quote: u64) -> Result<u64, u32> {
    let effective = sub(quote, 1)?;
    output(effective, c.virtual_quote_reserves, c.virtual_token_reserves)
}

fn buy_quote(c: &Case, amount: u64) -> Result<u64, u32> {
    let den = (c.virtual_token_reserves as u128).checked_sub(amount as u128).ok_or(OVERFLOW)?;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    u64::try_from(amount as u128 * c.virtual_quote_reserves as u128 / den + 1).map_err(|_| TRUNCATION)
}

fn net_of_bps(budget: u64, total_bps: u64) -> u64 {
    if total_bps == 0 {
        budget
    } else if budget == 0 {
        0
    } else {
        (budget as u128 * 10_000 / (10_000 + total_bps as u128)) as u64
    }
}

/// Largest net whose fees fit the budget, with the fees charged on that first
/// net. A curve without a creator gets no creator share in the divisor.
fn net_quote(c: &Case, bps: &TradeFees, budget: u64) -> Result<(u64, TradeFees), u32> {
    let creator_bps = if c.has_creator { bps.creator_bps } else { 0 };
    let total_bps = bps.protocol_bps.checked_add(creator_bps).ok_or(OVERFLOW)?;
    let mut net = net_of_bps(budget, total_bps);
    if net == 0 {
        return Err(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES);
    }
    let protocol = fee(net, bps.protocol_bps)?;
    let creator = fee(net, creator_bps)?;
    let total = net.saturating_add(protocol).saturating_add(creator);
    if total > budget {
        net = sub(net, total - budget)?;
        if net == 0 {
            return Err(BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT);
        }
    }
    Ok((net, TradeFees { protocol, creator, ..*bps }))
}

fn costs(c: &Case, tf: &Option<Fee>, quote: u64, fees: &TradeFees, post: Option<&Post>) -> Result<Costs, u32> {
    let buyback = buyback_split(c, fees.protocol).0;
    let post_buyback = post.map_or(0, |p| buyback_split(c, p.protocol_fee).0);
    let total_buyback = add(buyback, post_buyback)?;
    let first = add3(quote, fees.protocol, fees.creator)?;
    let second = match post {
        Some(p) => add3(p.quote_in, p.protocol_fee, p.creator_fee)?,
        None => 0,
    };
    let net = sub(add(first, second)?, total_buyback)?;
    let pool_quote = pre_fee(tf, net)?;
    Ok((pool_quote, total_buyback, sub(pool_quote, net)?))
}

fn cost_total(cost: &Costs) -> Result<u64, u32> {
    add(cost.0, cost.1)
}

/// Pool reserves the crossing fill prices against: the curve vault after the
/// curve fill, and the real quote plus the curve fill, less the native
/// migration fee.
fn pool_before(e: &ExactQuote, amount: u64, quote: u64) -> Result<(u64, u64), u32> {
    let c = &e.case;
    let pool_base = sub(c.curve_base, amount)?;
    let mut pool_quote = add(c.real_quote_reserves, quote)?;
    if c.native {
        pool_quote = sub(pool_quote, e.pool_migration_fee)?;
    }
    if pool_base == 0 {
        return Err(NOT_ENOUGH_TOKENS_TO_BUY);
    }
    if pool_quote == 0 {
        return Err(OVERFLOW);
    }
    Ok((pool_base, pool_quote))
}

fn estimate_post(c: &Case, pool: (u64, u64), bps: &TradeFees, budget: u64) -> Result<Option<Post>, u32> {
    let creator_bps = if c.has_creator { bps.creator_bps } else { 0 };
    let total_bps = bps.protocol_bps.checked_add(creator_bps).ok_or(OVERFLOW)?;
    if net_of_bps(budget, total_bps) < 2 {
        return Ok(None);
    }
    let (quote_in, fees) = net_quote(c, bps, budget)?;
    let base_out = output(sub(quote_in, 1)?, pool.1, pool.0)?;
    if base_out == 0 {
        return Ok(None);
    }
    Ok(Some(Post {
        base_out,
        quote_in,
        protocol_fee: fees.protocol,
        creator_fee: fees.creator,
        pool_base_before: pool.0,
        pool_quote_before: pool.1,
        buyback_fee: 0,
    }))
}

/// Shrinks the pool fill until the whole cost fits `budget`, or drops it.
fn fit_post(c: &Case, tf: &Option<Fee>, quote: u64, fees: &TradeFees, mut post: Post, budget: u64) -> Result<(Option<Post>, Costs), u32> {
    loop {
        let cost = costs(c, tf, quote, fees, Some(&post))?;
        let total = cost_total(&cost)?;
        if total <= budget {
            return Ok((Some(post), cost));
        }
        // 미확인 (unconfirmed): from here on, no captured case is over budget.
        match post.quote_in.checked_sub(total - budget).filter(|q| *q > 1) {
            Some(q) => post.quote_in = q,
            None => return Ok((None, costs(c, tf, quote, fees, None)?)),
        }
        post.base_out = output(post.quote_in - 1, post.pool_quote_before, post.pool_base_before)?;
        if post.base_out == 0 {
            return Ok((None, costs(c, tf, quote, fees, None)?));
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn execute(c: &Case, tf: &Option<Fee>, amount: u64, quote: u64, fees: &TradeFees, post: Option<Post>, cost: Costs, top_up: u64) -> Result<Filled, u32> {
    let vtr = sub(c.virtual_token_reserves, amount)?;
    let rtr = sub(c.real_token_reserves, amount)?;
    let vqr = add(c.virtual_quote_reserves, quote)?;
    let rqr = add(c.real_quote_reserves, quote)?;
    // A crossing keeps pool_base above the excess, so a vault that covers the
    // curve fill also covers the delivery; only the on-curve short is reachable.
    let delivered = add(amount, post.map_or(0, |p| p.base_out))?;
    if c.curve_base < delivered {
        return Err(TOKEN_INSUFFICIENT_FUNDS);
    }
    let (buyback, retained) = buyback_split(c, fees.protocol);
    let protocol_fees = add(c.protocol_fees, retained)?;
    let creator_fees = add(c.creator_fee, fees.creator)?;
    let (post_buyback, post_retained) = post.map_or((0, 0), |p| buyback_split(c, p.protocol_fee));
    let protocol_fees = add(protocol_fees, post_retained)?;
    let creator_fees = add(creator_fees, post.map_or(0, |p| p.creator_fee))?;
    let (pool_quote, total_buyback, quote_transfer_fee) = cost;
    let user_out = add(pool_quote, total_buyback)?;
    if !c.native && c.user_quote < user_out {
        return Err(TOKEN_INSUFFICIENT_FUNDS);
    }
    let curve_in = if c.native { pool_quote } else { post_fee(tf, pool_quote)? };
    let total_net = post_fee(tf, add(buyback, post_buyback)?)?;
    let post_net = post_fee(tf, post_buyback)?;
    Ok(Filled {
        settled: Settled {
            user_quote: -(user_out as i128),
            curve_quote: curve_in as i128,
            buyback_recipient: total_net as i128,
            rent_top_up: top_up,
            base_moved: amount,
            virtual_token_reserves: vtr,
            virtual_quote_reserves: vqr,
            real_token_reserves: rtr,
            real_quote_reserves: rqr,
            creator_fee: creator_fees,
            protocol_fees,
            quote,
            protocol_fee_bps: fees.protocol_bps,
            protocol_fee: fees.protocol,
            creator_fee_bps: fees.creator_bps,
            trade_creator_fee: fees.creator,
            buyback_fee_bps: if c.mayhem { 0 } else { c.buyback_bps },
            event_buyback_fee: sub(total_net, post_net)?,
            quote_transfer_fee,
            completes: rtr == 0,
        },
        post: post.map(|p| Post { buyback_fee: post_net, ..p }),
    })
}

fn buy_exact(e: &ExactQuote) -> Result<Filled, u32> {
    let c = &e.case;
    let top_up = rent_top_up(c)?;
    if c.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    if c.cashback {
        return Err(CASHBACK_COIN_NOT_SUPPORTED);
    }
    if c.limit == 0 {
        return Err(BUY_ZERO_AMOUNT);
    }
    if c.amount == 0 {
        return Err(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES);
    }
    let tf = active_fee(c);
    let available = post_fee(&tf, c.amount)?;
    if available == 0 {
        return Err(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES);
    }
    let fees = trade_fees(c, available)?;
    let (net_fees, tokens, net) = if c.whitelisted_user {
        (fees, tokens_for_quote(c, available)?, available)
    } else {
        let (net, net_fees) = net_quote(c, &fees, available)?;
        (net_fees, tokens_for_quote(c, net)?, net)
    };
    if tokens > c.real_token_reserves {
        let can_cross = !(c.mayhem || c.whitelisted_user);
        if !can_cross && !c.partial_fill {
            return Err(NOT_ENOUGH_TOKENS_TO_BUY);
        }
        let amount = c.real_token_reserves;
        let quote = buy_quote(c, amount)?;
        let curve_fees = trade_fees(c, quote)?;
        let base_cost = costs(c, &tf, quote, &curve_fees, None)?;
        // 미확인 (unconfirmed): for this handler; `buy_v3` confirms the code.
        if c.amount < cost_total(&base_cost)? {
            return Err(TOO_MUCH_SOL_REQUIRED);
        }
        let first = add3(quote, curve_fees.protocol, curve_fees.creator)?;
        let estimate = if can_cross && available > first {
            estimate_post(c, pool_before(e, amount, quote)?, &fees, available - first)?
        } else {
            None
        };
        let (post, cost) = match estimate {
            Some(post) => fit_post(c, &tf, quote, &curve_fees, post, c.amount)?,
            None => (None, base_cost),
        };
        // The minimum only binds a crossing buy; a partial fill takes what is left.
        if can_cross && add(amount, post.map_or(0, |p| p.base_out))? < c.limit {
            return Err(BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT);
        }
        return execute(c, &tf, amount, quote, &curve_fees, post, cost, top_up);
    }
    let (mut tokens, mut net) = (tokens, net);
    let mut cost = costs(c, &tf, net, &net_fees, None)?;
    let total = cost_total(&cost)?;
    if total > c.amount {
        // 미확인 (unconfirmed): no captured case enters this trim, so both codes
        // and the recomputed tokens and costs are unpinned.
        net = net.checked_sub(total - c.amount).ok_or(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES)?;
        if net == 0 {
            return Err(BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT);
        }
        tokens = tokens_for_quote(c, net)?;
        cost = costs(c, &tf, net, &net_fees, None)?;
    }
    if tokens < c.limit {
        return Err(BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT);
    }
    execute(c, &tf, tokens, net, &net_fees, None, cost, top_up)
}

/// `buy_v3` for more tokens than the curve holds: the excess is priced against
/// the pool with a ceiling, and fees are charged on that quote as well.
fn buy_crossing(e: &ExactQuote) -> Result<Filled, u32> {
    let c = &e.case;
    let top_up = rent_top_up(c)?;
    let amount = c.real_token_reserves;
    if amount == 0 {
        return Err(BUY_ZERO_AMOUNT);
    }
    let excess = c.amount - amount;
    let tf = active_fee(c);
    let quote = buy_quote(c, amount)?;
    let fees = trade_fees(c, quote)?;
    let (pool_base, pool_quote) = pool_before(e, amount, quote)?;
    if pool_base <= excess {
        return Err(NOT_ENOUGH_TOKENS_TO_BUY);
    }
    let den = (pool_base - excess) as u128;
    let quote_in = u64::try_from((excess as u128 * pool_quote as u128 + den - 1) / den).map_err(|_| TRUNCATION)?;
    let post_fees = trade_fees(c, quote_in)?;
    let post = Post {
        base_out: excess,
        quote_in,
        protocol_fee: post_fees.protocol,
        creator_fee: post_fees.creator,
        pool_base_before: pool_base,
        pool_quote_before: pool_quote,
        buyback_fee: 0,
    };
    let cost = costs(c, &tf, quote, &fees, Some(&post))?;
    if c.limit < cost_total(&cost)? {
        return Err(TOO_MUCH_SOL_REQUIRED);
    }
    execute(c, &tf, amount, quote, &fees, Some(post), cost, top_up)
}

pub fn run(e: &ExactQuote) -> Result<Filled, Option<u32>> {
    if e.case.whitelisted_user && e.case.mayhem {
        return Err(None);
    }
    buy_exact(e).map_err(Some)
}

pub fn run_buy(e: &ExactQuote) -> Result<Filled, Option<u32>> {
    let c = &e.case;
    if c.whitelisted_user && c.mayhem {
        return Err(None);
    }
    let can_cross = !(c.mayhem || c.whitelisted_user);
    if c.amount > c.real_token_reserves && can_cross && !c.complete && !c.cashback {
        return buy_crossing(e).map_err(Some);
    }
    match buy(c) {
        Outcome::Ok(settled) => Ok(Filled { settled, post: None }),
        Outcome::Error(code) => Err(Some(code)),
        Outcome::Unmodelled => Err(None),
    }
}
