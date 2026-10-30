//! Captured quote accounting of Pump `sell_v2`, `buy_v2` and
//! `buy_exact_quote_in_v2` on a token-quote curve (`quote_mint` set): wSOL, USDC,
//! other SPL Token mints and Token-2022 with or without a `TransferFeeConfig`.
//! The native SOL path of the same handlers is in `sell_v2.rs` and `buy_v2.rs`.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! with the captured Pump Fees program on LiteSVM by
//! `tests/test_v2_token_quote_captured.py`. A whitelisted user pays no fees and
//! closes the trade with the `mayhem_virtual_params.rs` resync.
//! Not linked into the SBF crate. This is not a byte-identity claim.
//!
//! The branches marked 미확인 (unconfirmed) are carried over from the program
//! sources: no captured run enters them, so their codes and arithmetic are not
//! pinned by this file.

use crate::mayhem_virtual_params as mayhem;

pub const NOT_AUTHORIZED: u32 = 6000;
pub const TOO_MUCH_SOL_REQUIRED: u32 = 6002;
pub const TOO_LITTLE_SOL_RECEIVED: u32 = 6003;
pub const MINT_DOES_NOT_MATCH_BONDING_CURVE: u32 = 6004;
pub const BONDING_CURVE_COMPLETE: u32 = 6005;
pub const ACCOUNT_TYPE_NOT_SUPPORTED: u32 = 6010;
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
/// Anchor `AccountNotInitialized`: the curve's quote account cannot be created.
pub const ACCOUNT_NOT_INITIALIZED: u32 = 3012;
/// Anchor `ConstraintSeeds`: a quote account is not the expected ATA.
pub const CONSTRAINT_SEEDS: u32 = 2006;
/// SPL Token / Token-2022 `InsufficientFunds`.
pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;

pub const CURVE_LEN: u64 = 166;
/// Zero-byte minimum: the whole amount is paid when the vault is below it.
pub const VAULT_RENT: u64 = 890_880;
pub fn rent(len: u64) -> u64 {
    (len + 128) * 6960
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Op {
    Sell,
    Buy,
    BuyExactQuoteIn,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum FeeTable {
    /// `fee_tiers`: wSOL.
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
    pub flat: (u64, u64),
    pub tiers: Vec<(u128, u64, u64)>,
    pub stable: Vec<(u128, u64, u64)>,
    pub exotic: (u64, u64, u64),
    pub len: u64,
}

/// A rejected quote token account.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum BadSlot {
    None,
    /// Not the expected ATA address.
    CurveKey,
    UserKey,
    VaultKey,
    AccumulatorKey,
    RecipientKey,
    BuybackKey,
    /// The curve's quote ATA does not exist.
    CurveMissing,
    /// The user's quote account has the wrong mint.
    UserMint,
}

#[derive(Clone, Debug)]
pub struct Case {
    pub op: Op,
    pub amount: u64,
    /// `min_sol_output` for a sell, `max_sol_cost` for a buy, `min_tokens_out`
    /// for the exact-quote buy.
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
    pub curve_lamports: u64,
    pub vault_lamports: u64,
    pub table: FeeTable,
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
    pub curve_quote: u64,
    pub fee_recipient_ok: bool,
    pub buyback_ok: bool,
    pub bad: BadSlot,
}

/// Amounts leave the source in full; what arrives is net of the Token-2022 fee.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Paid {
    pub sent: u64,
    pub received: u64,
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Settled {
    pub base_moved: u64,
    pub quote: u64,
    pub user: Paid,
    pub curve: Paid,
    /// Creator vault ATA, or the accumulator ATA on a cashback coin.
    pub creator: Paid,
    pub recipient: Paid,
    pub buyback: Paid,
    /// Zero-byte rent the user pays into the creator vault.
    pub vault_rent: u64,
    /// Lamports the user tops the curve up with to keep 166 bytes rent-exempt.
    pub curve_rent: u64,
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub protocol_fee_bps: u64,
    pub protocol_fee: u64,
    pub creator_fee_bps: u64,
    pub creator_fee: u64,
    pub buyback_fee_bps: u64,
    pub quote_transfer_fee: u64,
    pub completes: bool,
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
fn paid(fee: &Option<Fee>, sent: u64) -> Result<Paid, u32> {
    Ok(Paid { sent, received: post_fee(fee, sent)? })
}

fn tier(tiers: &[(u128, u64, u64)], market_cap: u128) -> Result<(u64, u64), u32> {
    let first = tiers.first().ok_or(FEE_TIERS_EMPTY_PANIC)?;
    let t = tiers.iter().rev().find(|t| market_cap >= t.0).unwrap_or(first);
    Ok((t.1, t.2))
}

/// Pump Fees `get_fees_with_quote_mint` failures, which the handlers pass on:
/// these are not custom codes, so the values only name them for the host.
pub const FEE_TIERS_EMPTY_PANIC: u32 = 90_001;
pub const FEE_CONFIG_INVALID_ACCOUNT_DATA: u32 = 90_002;

/// Rates from the Pump Fees CPI: (protocol_bps, creator_bps).
fn rates(c: &Case) -> Result<(u64, u64), u32> {
    let supply = if c.mayhem { c.token_total_supply } else { c.mint_supply };
    if c.virtual_token_reserves == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    let market_cap = supply as u128 * c.virtual_quote_reserves as u128 / c.virtual_token_reserves as u128;
    let f = &c.fee_config;
    if f.len < 2512 {
        return Err(FEE_CONFIG_INVALID_ACCOUNT_DATA);
    }
    let (protocol, base_creator) = match c.table {
        FeeTable::Tiers => tier(&f.tiers, market_cap)?,
        FeeTable::Stable => tier(if f.len > 4072 { &f.stable } else { &[] }, market_cap)?,
        FeeTable::Flat => {
            let e = f.exotic;
            if f.len > 4096 && (e.0 != 0 || e.1 != 0 || e.2 != 0) {
                (e.1, e.2)
            } else {
                f.flat
            }
        }
    };
    let creator = if c.creator_fee_configurable && c.curve_creator_fee_bps != 0 {
        c.curve_creator_fee_bps
    } else {
        base_creator
    };
    Ok((protocol, creator))
}

fn fee(amount: u64, basis_points: u64) -> Result<u64, u32> {
    let v = (amount as u128 * basis_points as u128 + 9_999) / 10_000;
    u64::try_from(v).map_err(|_| TRUNCATION)
}

/// (protocol_fee, creator_fee) on `quote`; the creator fee needs a creator.
fn fees(c: &Case, quote: u64, bps: (u64, u64)) -> Result<(u64, u64), u32> {
    Ok((fee(quote, bps.0)?, if c.has_creator { fee(quote, bps.1)? } else { 0 }))
}

fn buyback_split(c: &Case, protocol_fee: u64) -> (u64, u64) {
    if c.mayhem {
        return (0, protocol_fee);
    }
    let b = (c.buyback_bps as u128 * protocol_fee as u128 / 10_000) as u64;
    (b, protocol_fee - b)
}

/// The ATA address constraints run before anything else in the handlers.
fn addresses(c: &Case) -> Result<(), u32> {
    match c.bad {
        BadSlot::CurveKey | BadSlot::VaultKey | BadSlot::AccumulatorKey | BadSlot::RecipientKey | BadSlot::BuybackKey => {
            Err(CONSTRAINT_SEEDS)
        }
        _ => Ok(()),
    }
}

/// Pre-trade admission after the handler's input guards: recipients, then the
/// curve's and the user's quote accounts.
fn admission(c: &Case) -> Result<(), u32> {
    if !c.fee_recipient_ok {
        return Err(NOT_AUTHORIZED);
    }
    if !c.buyback_ok {
        return Err(BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED);
    }
    match c.bad {
        BadSlot::CurveMissing => Err(ACCOUNT_NOT_INITIALIZED),
        BadSlot::UserKey => Err(ACCOUNT_TYPE_NOT_SUPPORTED),
        BadSlot::UserMint => Err(MINT_DOES_NOT_MATCH_BONDING_CURVE),
        _ => Ok(()),
    }
}

fn curve_rent(c: &Case) -> u64 {
    rent(CURVE_LEN).saturating_sub(c.curve_lamports)
}

fn vault_rent(c: &Case, creator_fee: u64) -> u64 {
    if creator_fee > 0 && !c.cashback && c.vault_lamports < VAULT_RENT {
        VAULT_RENT
    } else {
        0
    }
}

pub fn sell(c: &Case) -> Result<Settled, u32> {
    addresses(c)?;
    if c.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    if c.amount == 0 {
        return Err(SELL_ZERO_AMOUNT);
    }
    if c.user_base < c.amount {
        return Err(NOT_ENOUGH_TOKENS_TO_SELL);
    }
    admission(c)?;
    let tf = active_fee(c);
    let den = c.virtual_token_reserves as u128 + c.amount as u128;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    let quote = u64::try_from(c.virtual_quote_reserves as u128 * c.amount as u128 / den).map_err(|_| TRUNCATION)?;
    let bps = if c.whitelisted_user { (0, 0) } else { rates(c)? };
    let (protocol_fee, creator_fee) = if c.whitelisted_user { (0, 0) } else { fees(c, quote, bps)? };
    let output = sub(sub(quote, protocol_fee)?, creator_fee)?;
    let net = post_fee(&tf, output)?;
    if net < c.limit {
        return Err(TOO_LITTLE_SOL_RECEIVED);
    }
    let vtr = add(c.virtual_token_reserves, c.amount)?;
    let rtr = add(c.real_token_reserves, c.amount)?;
    let vqr = sub(c.virtual_quote_reserves, quote)?;
    let rqr = sub(c.real_quote_reserves, quote)?;
    if c.curve_quote < quote {
        return Err(TOKEN_INSUFFICIENT_FUNDS);
    }
    let (buyback, retained) = buyback_split(c, protocol_fee);
    Ok(Settled {
        base_moved: c.amount,
        quote,
        user: paid(&tf, output)?,
        curve: Paid { sent: quote, received: 0 },
        creator: paid(&tf, creator_fee)?,
        recipient: paid(&tf, retained)?,
        buyback: paid(&tf, buyback)?,
        vault_rent: vault_rent(c, creator_fee),
        curve_rent: curve_rent(c),
        virtual_token_reserves: vtr,
        virtual_quote_reserves: vqr,
        real_token_reserves: rtr,
        real_quote_reserves: rqr,
        protocol_fee_bps: bps.0,
        protocol_fee,
        creator_fee_bps: bps.1,
        creator_fee,
        buyback_fee_bps: if c.mayhem { 0 } else { c.buyback_bps },
        quote_transfer_fee: sub(output, net)?,
        completes: false,
    })
}

fn settle_buy(c: &Case, amount: u64, quote: u64, gross: u64, protocol_fee: u64, creator_fee: u64, bps: (u64, u64)) -> Result<Settled, u32> {
    let tf = active_fee(c);
    if c.real_token_reserves < amount {
        return Err(NOT_ENOUGH_TOKENS_TO_BUY);
    }
    let vtr = sub(c.virtual_token_reserves, amount)?;
    let rtr = sub(c.real_token_reserves, amount)?;
    let vqr = add(c.virtual_quote_reserves, quote)?;
    let rqr = add(c.real_quote_reserves, quote)?;
    if c.curve_base < amount {
        return Err(TOKEN_INSUFFICIENT_FUNDS);
    }
    let cost = add(add(gross, protocol_fee)?, creator_fee)?;
    if c.user_quote < cost {
        return Err(TOKEN_INSUFFICIENT_FUNDS);
    }
    let (buyback, retained) = buyback_split(c, protocol_fee);
    Ok(Settled {
        base_moved: amount,
        quote,
        user: Paid { sent: cost, received: 0 },
        curve: paid(&tf, gross)?,
        creator: paid(&tf, creator_fee)?,
        recipient: paid(&tf, retained)?,
        buyback: paid(&tf, buyback)?,
        vault_rent: vault_rent(c, creator_fee),
        curve_rent: curve_rent(c),
        virtual_token_reserves: vtr,
        virtual_quote_reserves: vqr,
        real_token_reserves: rtr,
        real_quote_reserves: rqr,
        protocol_fee_bps: bps.0,
        protocol_fee,
        creator_fee_bps: bps.1,
        creator_fee,
        buyback_fee_bps: if c.mayhem { 0 } else { c.buyback_bps },
        quote_transfer_fee: sub(gross, quote)?,
        completes: rtr == 0,
    })
}

fn buy_quote(c: &Case, amount: u64) -> Result<u64, u32> {
    let den = (c.virtual_token_reserves as u128).checked_sub(amount as u128).ok_or(OVERFLOW)?;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    u64::try_from(amount as u128 * c.virtual_quote_reserves as u128 / den + 1).map_err(|_| TRUNCATION)
}

pub fn buy(c: &Case) -> Result<Settled, u32> {
    addresses(c)?;
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
    admission(c)?;
    let tf = active_fee(c);
    let quote = buy_quote(c, amount)?;
    let gross = pre_fee(&tf, quote)?;
    sub(gross, quote)?;
    let bps = if c.whitelisted_user { (0, 0) } else { rates(c)? };
    let (protocol_fee, creator_fee) = if c.whitelisted_user { (0, 0) } else { fees(c, quote, bps)? };
    if c.limit < add(add(gross, protocol_fee)?, creator_fee)? {
        return Err(TOO_MUCH_SOL_REQUIRED);
    }
    settle_buy(c, amount, quote, gross, protocol_fee, creator_fee, bps)
}

fn tokens_for_quote(c: &Case, quote: u64) -> Result<u64, u32> {
    let effective = quote.checked_sub(1).ok_or(OVERFLOW)? as u128;
    let den = c.virtual_quote_reserves as u128 + effective;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    u64::try_from(effective * c.virtual_token_reserves as u128 / den).map_err(|_| TRUNCATION)
}

pub fn buy_exact_quote_in(c: &Case) -> Result<Settled, u32> {
    addresses(c)?;
    if c.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    if c.limit == 0 {
        return Err(BUY_ZERO_AMOUNT);
    }
    if c.amount == 0 {
        return Err(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES);
    }
    admission(c)?;
    let tf = active_fee(c);
    let input = c.amount;
    let available = post_fee(&tf, input)?;
    if available == 0 {
        return Err(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES);
    }
    let (quote, protocol_fee, creator_fee, computed, bps) = if c.whitelisted_user {
        (available, 0, 0, tokens_for_quote(c, available)?, (0, 0))
    } else {
        let bps = rates(c)?;
        // Both fees are sized on the whole budget first: only their 6025 shows.
        fees(c, available, bps)?;
        let total_bps = bps.0.checked_add(if c.has_creator { bps.1 } else { 0 }).ok_or(OVERFLOW)?;
        let raw = if total_bps == 0 { available } else { (available as u128 * 10_000 / (10_000 + total_bps as u128)) as u64 };
        if raw == 0 {
            return Err(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES);
        }
        let (protocol_fee, creator_fee) = fees(c, raw, bps)?;
        let total = raw.saturating_add(protocol_fee).saturating_add(creator_fee);
        let mut quote = raw;
        if total > available {
            quote = raw.checked_sub(total - available).ok_or(OVERFLOW)?;
            if quote == 0 {
                return Err(BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT);
            }
        }
        (quote, protocol_fee, creator_fee, tokens_for_quote(c, quote)?, bps)
    };
    let gross_total = |quote: u64, pf: u64, cf: u64| -> Result<(u64, u64), u32> {
        let gross = pre_fee(&tf, quote)?;
        Ok((gross, add(add(gross, pf)?, cf)?))
    };
    if computed > c.real_token_reserves && c.partial_fill {
        let amount = c.real_token_reserves;
        let quote = buy_quote(c, amount)?;
        let (protocol_fee, creator_fee) = if c.whitelisted_user { (0, 0) } else { fees(c, quote, bps)? };
        let (gross, total) = gross_total(quote, protocol_fee, creator_fee)?;
        if input < total {
            // 미확인: no captured run enters this; the partial fill never costs more than the budget here.
            return Err(TOO_MUCH_SOL_REQUIRED);
        }
        return settle_buy(c, amount, quote, gross, protocol_fee, creator_fee, bps);
    }
    let (mut gross, total) = gross_total(quote, protocol_fee, creator_fee)?;
    let (mut quote, mut amount) = (quote, computed);
    if total > input {
        // 미확인: the net and fees are sized to `available`, and the gross-up
        // never exceeds what the budget gave up to the transfer fee on the
        // inputs tried, so this trim has not run on the captured program.
        quote = quote.checked_sub(total - input).ok_or(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES)?;
        if quote == 0 {
            return Err(BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT);
        }
        amount = tokens_for_quote(c, quote)?;
        gross = gross_total(quote, protocol_fee, creator_fee)?.0;
    }
    if amount < c.limit {
        return Err(BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT);
    }
    settle_buy(c, amount, quote, gross, protocol_fee, creator_fee, bps)
}

/// The stored virtual quote reserve after a whitelisted trade: the resync reads
/// the settled curve, not yet marked complete, and the curve's and the user's
/// base balances.
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
        native_quote: false,
    };
    mayhem::sync(&curve, curve_base, user_base)
}

pub fn run(c: &Case) -> Result<Settled, u32> {
    let mut s = match c.op {
        Op::Sell => sell(c),
        Op::Buy => buy(c),
        Op::BuyExactQuoteIn => buy_exact_quote_in(c),
    }?;
    if c.whitelisted_user {
        s.virtual_quote_reserves = resync(c, &s)?;
    }
    Ok(s)
}
