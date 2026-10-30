//! Captured Pump rules of a single `multi_hop_curve_swap` hop: the pre-loop
//! argument checks, the hop admission gates, and the exact-in buy / sell
//! accounting of one curve with each of the four hop fee flags (bit 0
//! protocol fee, bit 1 creator fee), for a native-SOL and an SPL-token quote
//! curve.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_multi_hop_hop_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Unconfirmed (outside the checked inputs): buys that cross into the
//! post-complete fill (`Outcome::Unmodelled`), routes of two or more hops,
//! Token-2022 quote mints, more than one fee tier, a configurable creator
//! fee, and the account-level checks (signer, FeeConfig owner, ATAs,
//! buyback recipient) that run before or around the arithmetic.

pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;
pub const BONDING_CURVE_COMPLETE: u32 = 6005;
pub const BUY_ZERO_AMOUNT: u32 = 6020;
pub const SELL_ZERO_AMOUNT: u32 = 6022;
pub const OVERFLOW: u32 = 6024;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: u32 = 6027;
pub const BUY_NOT_ENOUGH_SOL_TO_COVER_FEES: u32 = 6041;
pub const BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT: u32 = 6042;
pub const CASHBACK_COIN_NOT_SUPPORTED: u32 = 6094;
pub const FEE_TIERS_EMPTY: u32 = 6096;
pub const FEE_CONFIG_TOO_SHORT: u32 = 6097;
pub const HOP_FEES_MISMATCH: u32 = 6106;
pub const MAYHEM_CURVE_NOT_SUPPORTED: u32 = 6108;

pub struct Hop {
    pub buy: bool,
    pub native: bool,
    pub amount_in: u64,
    /// Raw `hop_fees` argument.
    pub hop_fees: Vec<u8>,
    pub remaining_accounts: usize,
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub complete: bool,
    pub mayhem: bool,
    pub cashback: bool,
    pub has_creator: bool,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    /// FeeConfig length and whether its table (SOL tiers or flat fees) is empty.
    pub fee_config_len: usize,
    pub fee_table_empty: bool,
    /// (protocol, creator) basis points of the one fee tier / flat entry.
    pub fee_bps: (u64, u64),
    pub buyback_bps: u64,
    /// Base tokens the user holds (sell input).
    pub user_base: u64,
    /// Quote tokens the curve's quote ATA holds (SPL route).
    pub curve_quote_tokens: u64,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Settled {
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    /// Base tokens moved (out of the curve on a buy, into it on a sell).
    pub base: u64,
    /// Quote the user receives on a sell (0 on a buy).
    pub output: u64,
    /// Quote paid to the buyback recipient (only with the protocol bit).
    pub buyback: u64,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Outcome {
    Ok(Settled),
    Error(u32),
    /// The buy crosses into the post-complete fill.
    Unmodelled,
}

fn fee(amount: u64, bps: u64) -> Result<u64, u32> {
    u64::try_from((amount as u128 * bps as u128 + 9_999) / 10_000).map_err(|_| OVERFLOW)
}

fn sub(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_sub(b).ok_or(OVERFLOW)
}

fn add(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_add(b).ok_or(OVERFLOW)
}

pub fn run(h: &Hop) -> Outcome {
    match hop(h) {
        Ok(Some(s)) => Outcome::Ok(s),
        Ok(None) => Outcome::Unmodelled,
        Err(code) => Outcome::Error(code),
    }
}

fn hop(h: &Hop) -> Result<Option<Settled>, u32> {
    // Pre-loop argument checks, in this order.
    if h.amount_in == 0 {
        return Err(BUY_ZERO_AMOUNT);
    }
    let count = h.remaining_accounts / 5;
    if h.remaining_accounts < 5 || count * 5 != h.remaining_accounts {
        return Err(NOT_ENOUGH_REMAINING_ACCOUNTS);
    }
    if h.hop_fees.len() != count || h.hop_fees.iter().any(|&f| f >= 4) {
        return Err(HOP_FEES_MISMATCH);
    }
    let flag = h.hop_fees[0];
    // Hop admission.
    if h.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    // A cashback coin is refused only when the hop charges the creator fee.
    if h.cashback && flag & 2 != 0 {
        return Err(CASHBACK_COIN_NOT_SUPPORTED);
    }
    if h.mayhem {
        return Err(MAYHEM_CURVE_NOT_SUPPORTED);
    }
    // Fees are selected even when the flag charges none.
    if h.fee_config_len < 2512 {
        return Err(FEE_CONFIG_TOO_SHORT);
    }
    if h.fee_table_empty {
        return Err(FEE_TIERS_EMPTY);
    }
    let p_rate = if flag & 1 != 0 { h.fee_bps.0 } else { 0 };
    let c_rate = if flag & 2 != 0 { h.fee_bps.1 } else { 0 };
    let c_rate = if h.has_creator { c_rate } else { 0 };
    let (base, quote, pf, cf, output) = if h.buy {
        // Net quote for an exact-in budget, then trimmed so net + fees fit.
        let budget = h.amount_in;
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
        // The curve is priced on budget - fees, not on the trimmed net.
        let q = sub(sub(budget, pf)?, cf)?;
        // q >= net >= 1 here, so this subtraction cannot fail (unconfirmed path).
        let effective = sub(q, 1)? as u128;
        let base = effective * h.virtual_token_reserves as u128 / (h.virtual_quote_reserves as u128 + effective);
        let base = u64::try_from(base).map_err(|_| OVERFLOW)?;
        if base == 0 {
            return Err(BUY_ZERO_AMOUNT);
        }
        if base > h.real_token_reserves {
            return Ok(None);
        }
        (base, q, pf, cf, 0)
    } else {
        let amount = h.amount_in;
        let gross = (h.virtual_quote_reserves as u128 * amount as u128
            / (h.virtual_token_reserves as u128 + amount as u128)) as u64;
        // Sell fees are computed on the gross quote and then masked by the flag.
        let pf = if flag & 1 != 0 { fee(gross, h.fee_bps.0)? } else { 0 };
        let cf = if flag & 2 != 0 && h.has_creator { fee(gross, h.fee_bps.1)? } else { 0 };
        let net = sub(sub(gross, pf)?, cf)?;
        if net == 0 {
            return Err(SELL_ZERO_AMOUNT);
        }
        if h.user_base < amount {
            return Err(TOKEN_INSUFFICIENT_FUNDS);
        }
        (amount, gross, pf, cf, net)
    };
    let (vtr, rtr, vqr, rqr) = if h.buy {
        (sub(h.virtual_token_reserves, base)?, sub(h.real_token_reserves, base)?,
         add(h.virtual_quote_reserves, quote)?, add(h.real_quote_reserves, quote)?)
    } else {
        (add(h.virtual_token_reserves, base)?, add(h.real_token_reserves, base)?,
         sub(h.virtual_quote_reserves, quote)?, sub(h.real_quote_reserves, quote)?)
    };
    let buyback = (h.buyback_bps as u128 * pf as u128 / 10_000) as u64;
    let protocol_fees = add(h.protocol_fees, pf - buyback)?;
    let creator_fee = add(h.creator_fee, cf)?;
    if !h.native && !h.buy && h.curve_quote_tokens < output {
        return Err(TOKEN_INSUFFICIENT_FUNDS);
    }
    Ok(Some(Settled {
        virtual_token_reserves: vtr,
        virtual_quote_reserves: vqr,
        real_token_reserves: rtr,
        real_quote_reserves: rqr,
        creator_fee,
        protocol_fees,
        base,
        output,
        buyback,
    }))
}
