//! Captured Pump rules of which fee rates each `multi_hop_curve_swap` hop charges:
//! the FeeConfig table its quote mint selects, the tier the hop's own market cap
//! lands on, the account lengths that gate the tables, and a curve's configurable
//! creator fee. `multi_hop_route.rs` fixes one rate per route and leaves these out;
//! the rest of the swap here is the same as in that file.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_multi_hop_fees_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): Token-2022 mints, Mayhem
//! market caps (the swap refuses those curves), curves that need a rent top-up,
//! and the account-level checks other than the recipient mint.

pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;
/// A last hop transfers before the destination mint is compared, so SPL Token
/// refuses a wrong destination; only a native sell reaches `DISCONTINUOUS_PATH`.
pub const TOKEN_MINT_MISMATCH: u32 = 3;
pub const MINT_DOES_NOT_MATCH_BONDING_CURVE: u32 = 6004;
pub const BONDING_CURVE_COMPLETE: u32 = 6005;
pub const BUY_ZERO_AMOUNT: u32 = 6020;
pub const SELL_ZERO_AMOUNT: u32 = 6022;
pub const OVERFLOW: u32 = 6024;
pub const TRUNCATION: u32 = 6025;
pub const DIVISION_BY_ZERO: u32 = 6026;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: u32 = 6027;
pub const BUY_NOT_ENOUGH_SOL_TO_COVER_FEES: u32 = 6041;
pub const BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT: u32 = 6042;
pub const NOT_ENOUGH_TOKENS_TO_BUY: u32 = 6021;
pub const CASHBACK_COIN_NOT_SUPPORTED: u32 = 6094;
pub const DISCONTINUOUS_PATH: u32 = 6098;
pub const HOP_FEES_MISMATCH: u32 = 6106;
pub const MAYHEM_CURVE_NOT_SUPPORTED: u32 = 6108;
pub const FEE_TIERS_EMPTY: u32 = 6096;
pub const FEE_CONFIG_TOO_SHORT: u32 = 6097;

/// Mint id of wrapped SOL; a curve quoted in it holds native lamports.
pub const NATIVE: u8 = 0;
/// Mint ids of the two token quotes that do not use the flat fees.
pub const USDC: u8 = 5;
pub const SOL_LIKE: u8 = 6;

/// One tier: market cap threshold, protocol bps, creator bps.
pub type Tier = (u128, u64, u64);

#[derive(Clone, Debug, Default)]
pub struct FeeConfig {
    pub len: usize,
    pub tiers: Vec<Tier>,
    pub stable: Vec<Tier>,
    pub flat: (u64, u64),
    /// LP, protocol and creator bps.
    pub exotic: (u64, u64, u64),
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Curve {
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    pub post_complete_base_out: u64,
    pub post_complete_quote_in: u64,
    pub has_creator: bool,
    pub cashback: bool,
    pub complete: bool,
    pub mayhem: bool,
    pub creator_fee_bps: u64,
    pub base_mint: u8,
    pub quote_mint: u8,
    pub base_vault: u64,
    pub quote_vault: u64,
    /// Signed change of the lamports a native curve holds.
    pub lamports: i128,
}

#[derive(Clone, Debug)]
pub struct Route {
    pub amount_in: u64,
    pub hop_fees: Vec<u8>,
    pub remaining_accounts: usize,
    pub source_mint: u8,
    pub destination_mint: u8,
    pub source_balance: u64,
    pub recipient_mint: u8,
    pub pool_migration_fee: u64,
    pub buyback_bps: u64,
    pub fee_config: FeeConfig,
    pub creator_fee_configurable: bool,
    pub mint_supply: u64,
    /// Curve index of each hop; a route may visit a curve twice.
    pub hops: Vec<usize>,
    pub curves: Vec<Curve>,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Settled {
    pub amount_out: u64,
    pub buyback_fee: u64,
    pub source: i128,
    pub destination: i128,
    pub user_lamports: i128,
    pub recipient: u64,
    pub curves: Vec<Curve>,
}

fn add(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_add(b).ok_or(OVERFLOW)
}
fn sub(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_sub(b).ok_or(OVERFLOW)
}
fn fee(amount: u64, bps: u64) -> Result<u64, u32> {
    u64::try_from((amount as u128 * bps as u128 + 9_999) / 10_000).map_err(|_| TRUNCATION)
}
fn output(amount_in: u64, reserve_in: u64, reserve_out: u64) -> Result<u64, u32> {
    let den = reserve_in as u128 + amount_in as u128;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    u64::try_from(amount_in as u128 * reserve_out as u128 / den).map_err(|_| TRUNCATION)
}
fn buy_quote(c: &Curve, amount: u64) -> Result<u64, u32> {
    let den = (c.virtual_token_reserves as u128).checked_sub(amount as u128).ok_or(OVERFLOW)?;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    u64::try_from(amount as u128 * c.virtual_quote_reserves as u128 / den + 1).map_err(|_| TRUNCATION)
}

/// (net, protocol fee, creator fee) of a budget: the fees are charged on the
/// first net, and the net is trimmed if they do not fit. Callers price on
/// `budget - fees`, not on the trimmed net.
fn net_quote(p_rate: u64, c_rate: u64, budget: u64) -> Result<(u64, u64, u64), u32> {
    let total = p_rate + c_rate;
    let mut net = if total == 0 { budget } else { (budget as u128 * 10_000 / (10_000 + total as u128)) as u64 };
    if net == 0 {
        return Err(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES);
    }
    let pf = fee(net, p_rate)?;
    let cf = fee(net, c_rate)?;
    let all = net.saturating_add(pf).saturating_add(cf);
    if all > budget {
        net = sub(net, all - budget)?;
        if net == 0 {
            return Err(BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT);
        }
    }
    Ok((net, pf, cf))
}

struct PostFill {
    base_out: u64,
    quote_in: u64,
    pf: u64,
    cf: u64,
}

/// The crossing fill: the rest of the budget after the curve is filled, priced
/// against the pool on `budget - fees` with the unmasked-by-creator rates.
fn complete_fill(r: &Route, c: &Curve, flag: u8, bps: (u64, u64), rates: (u64, u64), budget: u64) -> Result<Option<(u64, u64, u64, PostFill)>, u32> {
    let quote = buy_quote(c, c.real_token_reserves)?;
    let pf = if flag & 1 != 0 { fee(quote, bps.0)? } else { 0 };
    let cf = if flag & 2 != 0 && c.has_creator { fee(quote, bps.1)? } else { 0 };
    let total = add(add(quote, pf)?, cf)?;
    let remaining = match budget.checked_sub(total) {
        Some(v) if v > 0 => v,
        _ => return Ok(None),
    };
    let pool_base = sub(c.base_vault, c.real_token_reserves)?;
    let mut pool_quote = add(c.real_quote_reserves, quote)?;
    if c.quote_mint == NATIVE {
        pool_quote = sub(pool_quote, r.pool_migration_fee)?;
    }
    if pool_base == 0 {
        return Err(NOT_ENOUGH_TOKENS_TO_BUY);
    }
    if pool_quote == 0 {
        return Err(OVERFLOW);
    }
    let total_bps = rates.0 + rates.1;
    let net = if total_bps == 0 { remaining } else { (remaining as u128 * 10_000 / (10_000 + total_bps as u128)) as u64 };
    if net < 2 {
        return Ok(None);
    }
    let (_, post_pf, post_cf) = net_quote(rates.0, rates.1, remaining)?;
    let quote_in = sub(sub(remaining, post_pf)?, post_cf)?;
    let base_out = output(sub(quote_in, 1)?, pool_quote, pool_base)?;
    if base_out == 0 {
        return Ok(None);
    }
    Ok(Some((quote, pf, cf, PostFill { base_out, quote_in, pf: post_pf, cf: post_cf })))
}

fn tier(tiers: &[Tier], market_cap: u128) -> Result<(u64, u64), u32> {
    let first = tiers.first().ok_or(FEE_TIERS_EMPTY)?;
    if market_cap < first.0 {
        return Ok((first.1, first.2));
    }
    let t = tiers.iter().rev().find(|t| market_cap >= t.0).unwrap_or(first);
    Ok((t.1, t.2))
}

/// Market cap of the curve as this hop finds it, so a later visit may land on
/// another tier.
fn market_cap(r: &Route, c: &Curve) -> Result<u128, u32> {
    if c.virtual_token_reserves == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    Ok(r.mint_supply as u128 * c.virtual_quote_reserves as u128 / c.virtual_token_reserves as u128)
}

/// (protocol, creator) basis points of a hop. USDC reads its tiers only past
/// 4,072 bytes, and non-zero exotic fees replace the flat fees only past 4,096.
///
/// Both fees are computed on `amount` before the hop's flags are looked at, so a
/// rate that truncates fails a hop that would not have charged it.
fn rates(r: &Route, c: &Curve, cap: u128, amount: u64) -> Result<(u64, u64), u32> {
    let f = &r.fee_config;
    if f.len < 2512 {
        return Err(FEE_CONFIG_TOO_SHORT);
    }
    let (protocol, creator) = match c.quote_mint {
        NATIVE | SOL_LIKE => tier(&f.tiers, cap)?,
        USDC => tier(if f.len > 4072 { &f.stable } else { &[] }, cap)?,
        _ => {
            let e = f.exotic;
            if f.len > 4096 && (e.0 != 0 || e.1 != 0 || e.2 != 0) { (e.1, e.2) } else { f.flat }
        }
    };
    let creator = if r.creator_fee_configurable && c.creator_fee_bps != 0 { c.creator_fee_bps } else { creator };
    fee(amount, protocol)?;
    if c.has_creator {
        fee(amount, creator)?;
    }
    Ok((protocol, creator))
}

fn take(balance: &mut u64, amount: u64) -> Result<(), u32> {
    *balance = balance.checked_sub(amount).ok_or(TOKEN_INSUFFICIENT_FUNDS)?;
    Ok(())
}

/// Where the previous hop left its output: (curve index, base vault?).
type Vault = Option<(usize, bool)>;

struct Hop {
    mint: u8,
    amount: u64,
    buyback: u64,
    vault: (usize, bool),
}

fn pay_in(r: &mut Route, s: &mut Settled, previous: Vault, to: (usize, bool), amount: u64) -> Result<(), u32> {
    match previous {
        None => {
            take(&mut r.source_balance, amount)?;
            s.source -= amount as i128;
        }
        // A vault already holding the input moves nothing.
        Some(from) if from == to => return Ok(()),
        Some((i, base)) => {
            let c = &mut r.curves[i];
            take(if base { &mut c.base_vault } else { &mut c.quote_vault }, amount)?;
        }
    }
    let c = &mut r.curves[to.0];
    let v = if to.1 { &mut c.base_vault } else { &mut c.quote_vault };
    *v = v.saturating_add(amount);
    Ok(())
}

fn swap_hop(r: &mut Route, s: &mut Settled, idx: usize, current: u8, amount: u64, previous: Vault, last: bool, flag: u8) -> Result<Hop, u32> {
    let c = r.curves[idx].clone();
    if c.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    // A cashback coin is refused only when the hop charges the creator fee.
    if c.cashback && flag & 2 != 0 {
        return Err(CASHBACK_COIN_NOT_SUPPORTED);
    }
    if c.mayhem {
        return Err(MAYHEM_CURVE_NOT_SUPPORTED);
    }
    if flag & 1 != 0 && r.recipient_mint != c.quote_mint {
        return Err(MINT_DOES_NOT_MATCH_BONDING_CURVE);
    }
    let buy = if current == c.quote_mint {
        true
    } else if current == c.base_mint {
        false
    } else {
        return Err(DISCONTINUOUS_PATH);
    };
    let native = c.quote_mint == NATIVE;
    let cap = market_cap(r, &c)?;
    let (pf, cf, out, post) = if buy {
        let bps = rates(r, &c, cap, amount)?;
        let p_rate = if flag & 1 != 0 { bps.0 } else { 0 };
        let c_rate = if flag & 2 != 0 && c.has_creator { bps.1 } else { 0 };
        let (_, nf_p, nf_c) = net_quote(p_rate, c_rate, amount)?;
        let q = sub(sub(amount, nf_p)?, nf_c)?;
        let base = output(sub(q, 1)?, c.virtual_quote_reserves, c.virtual_token_reserves)?;
        if base == 0 {
            return Err(BUY_ZERO_AMOUNT);
        }
        let reserves = c.real_token_reserves;
        let (base_amount, quote_amount, pf, cf, post) = if base > reserves {
            match complete_fill(r, &c, flag, bps, (p_rate, c_rate), amount)? {
                None => (reserves, q, nf_p, nf_c, None),
                Some((quote, f_p, f_c, post)) => (reserves, quote, f_p, f_c, Some(post)),
            }
        } else {
            (base, q, nf_p, nf_c, None)
        };
        let raw = add(base_amount, post.as_ref().map_or(0, |p| p.base_out))?;
        if native {
            s.user_lamports -= amount as i128;
            r.curves[idx].lamports += amount as i128;
        } else {
            pay_in(r, s, previous, (idx, false), amount)?;
        }
        let c = &mut r.curves[idx];
        c.virtual_token_reserves = sub(c.virtual_token_reserves, base_amount)?;
        c.real_token_reserves = sub(c.real_token_reserves, base_amount)?;
        c.virtual_quote_reserves = add(c.virtual_quote_reserves, quote_amount)?;
        c.real_quote_reserves = add(c.real_quote_reserves, quote_amount)?;
        if last {
            take(&mut c.base_vault, raw)?;
            if r.destination_mint != c.base_mint {
                return Err(TOKEN_MINT_MISMATCH);
            }
            s.destination += raw as i128;
        }
        (pf, cf, raw, post)
    } else {
        let gross = u64::try_from(c.virtual_quote_reserves as u128 * amount as u128 / (c.virtual_token_reserves as u128 + amount as u128)).map_err(|_| TRUNCATION)?;
        let bps = rates(r, &c, cap, gross)?;
        let pf = if flag & 1 != 0 { fee(gross, bps.0)? } else { 0 };
        let cf = if flag & 2 != 0 && c.has_creator { fee(gross, bps.1)? } else { 0 };
        let net = sub(sub(gross, pf)?, cf)?;
        if net == 0 {
            return Err(SELL_ZERO_AMOUNT);
        }
        pay_in(r, s, previous, (idx, true), amount)?;
        let c = &mut r.curves[idx];
        c.virtual_token_reserves = add(c.virtual_token_reserves, amount)?;
        c.real_token_reserves = add(c.real_token_reserves, amount)?;
        c.virtual_quote_reserves = sub(c.virtual_quote_reserves, gross)?;
        c.real_quote_reserves = sub(c.real_quote_reserves, gross)?;
        if last && !native {
            take(&mut c.quote_vault, net)?;
            if r.destination_mint != c.quote_mint {
                return Err(TOKEN_MINT_MISMATCH);
            }
            s.destination += net as i128;
        }
        (pf, cf, net, None)
    };
    let split = |p: u64| (r.buyback_bps as u128 * p as u128 / 10_000) as u64;
    let buyback = split(pf);
    let post_buyback = post.as_ref().map_or(0, |p| split(p.pf));
    let c = &mut r.curves[idx];
    c.protocol_fees = add(c.protocol_fees, pf - buyback)?;
    c.creator_fee = add(c.creator_fee, cf)?;
    if let Some(p) = &post {
        c.post_complete_base_out = p.base_out;
        c.post_complete_quote_in = p.quote_in;
        c.protocol_fees = add(c.protocol_fees, p.pf - post_buyback)?;
        c.creator_fee = add(c.creator_fee, p.cf)?;
    }
    let paid = add(buyback, post_buyback)?;
    if flag & 1 != 0 {
        if native {
            c.lamports -= paid as i128;
        } else {
            take(&mut c.quote_vault, paid)?;
        }
        s.recipient = add(s.recipient, paid)?;
    }
    if native && !buy && last {
        c.lamports -= out as i128;
        s.user_lamports += out as i128;
    }
    if c.real_token_reserves == 0 {
        c.complete = true;
    }
    Ok(if buy {
        Hop { mint: c.base_mint, amount: out, buyback: paid, vault: (idx, true) }
    } else {
        Hop { mint: c.quote_mint, amount: out, buyback: paid, vault: (idx, false) }
    })
}

pub fn run(route: &Route) -> Result<Settled, u32> {
    let mut r = route.clone();
    if r.amount_in == 0 {
        return Err(BUY_ZERO_AMOUNT);
    }
    let count = r.remaining_accounts / 5;
    if r.remaining_accounts < 5 || count * 5 != r.remaining_accounts {
        return Err(NOT_ENOUGH_REMAINING_ACCOUNTS);
    }
    if r.hop_fees.len() != count || r.hop_fees.iter().any(|&f| f >= 4) {
        return Err(HOP_FEES_MISMATCH);
    }
    let mut s = Settled {
        amount_out: 0,
        buyback_fee: 0,
        source: 0,
        destination: 0,
        user_lamports: 0,
        recipient: 0,
        curves: vec![],
    };
    let (mut current, mut amount, mut previous, mut total) = (r.source_mint, r.amount_in, None, 0u64);
    for i in 0..count {
        let (idx, flag) = (r.hops[i], r.hop_fees[i]);
        let out = swap_hop(&mut r, &mut s, idx, current, amount, previous, i + 1 == count, flag)?;
        previous = Some(out.vault);
        current = out.mint;
        amount = out.amount;
        total = add(total, out.buyback)?;
    }
    if current != r.destination_mint {
        return Err(DISCONTINUOUS_PATH);
    }
    s.amount_out = amount;
    s.buyback_fee = total;
    s.curves = r.curves;
    Ok(s)
}
