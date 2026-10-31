//! Captured accounting of Pump `sell_v2`, `buy_v2` and `buy_exact_quote_in_v2`
//! on the native Mayhem and holder-reward coins that `sell_v2.rs` and
//! `buy_v2.rs` leave out, expressed on top of those two models. A Mayhem curve
//! takes its protocol fee to a reserved recipient with no buyback split and
//! prices its fee tier on `token_total_supply`; a holder-reward coin repeats its
//! creator fee in the TradeEvent holder fields. A regular user gets no resync.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_v2_mayhem_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.

use crate::buy_v2;
use crate::legacy_buy as buy;
use crate::legacy_sell as sell;
use crate::sell_v2;

/// The fee-recipient account the instruction names.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Recipient {
    /// `Global.fee_recipient`.
    Regular,
    /// `Global.reserved_fee_recipient` or a `reserved_fee_recipients` entry.
    Reserved,
    /// Any other key.
    Other,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Op {
    Sell,
    Buy,
    BuyExactQuoteIn,
}

#[derive(Clone, Debug)]
pub struct Case {
    pub op: Op,
    pub amount: u64,
    /// `min_sol_output`, `max_sol_cost` or `min_tokens_out`.
    pub limit: u64,
    pub trailing: Vec<u8>,
    pub virtual_token_reserves: u64,
    pub virtual_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub real_sol_reserves: u64,
    pub token_total_supply: u64,
    pub complete: bool,
    pub mayhem: bool,
    pub holder_reward: bool,
    pub has_creator: bool,
    pub curve_creator_bps: u64,
    pub creator_fee_configurable: bool,
    pub mint_supply: u64,
    pub buyback_bps: u64,
    pub vault_lamports: u64,
    pub user_tokens: u64,
    pub tiers: Vec<buy::Tier>,
    pub recipient: Recipient,
    pub buyback_ok: bool,
}

/// Fields of either fill that the captured program exposes.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Settled {
    pub tokens: u64,
    pub sol_amount: u64,
    pub protocol_bps: u64,
    pub protocol_fee: u64,
    pub creator_bps: u64,
    pub creator_fee: u64,
    pub buyback_fee: u64,
    /// Lamports the creator vault receives, including any rent top-up.
    pub vault_credit: u64,
    /// Lamports the user pays (negative) or receives, before the transaction fee.
    pub user_delta: i128,
    pub virtual_token_reserves: u64,
    pub virtual_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub real_sol_reserves: u64,
    pub completes: bool,
    pub holder_rewards_bps: u64,
    pub holder_rewards: u64,
    pub buyback_bps: u64,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    Code(u32),
    Panic,
}

impl From<buy::Stop> for Stop {
    fn from(stop: buy::Stop) -> Self {
        match stop {
            buy::Stop::Code(code) => Stop::Code(code),
            buy::Stop::Panic => Stop::Panic,
        }
    }
}

impl From<sell::Stop> for Stop {
    fn from(stop: sell::Stop) -> Self {
        match stop {
            sell::Stop::Code(code) => Stop::Code(code),
            sell::Stop::Panic => Stop::Panic,
        }
    }
}

/// A Mayhem curve accepts only reserved recipients, any other curve only the
/// regular one.
fn recipient_ok(c: &Case) -> bool {
    if c.mayhem {
        c.recipient == Recipient::Reserved
    } else {
        c.recipient == Recipient::Regular
    }
}

fn supply(c: &Case) -> u64 {
    if c.mayhem {
        c.token_total_supply
    } else {
        c.mint_supply
    }
}

fn buyback_bps(c: &Case) -> u64 {
    if c.mayhem {
        0
    } else {
        c.buyback_bps
    }
}

fn run_buy(c: &Case) -> Result<Settled, Stop> {
    let curve = buy::Curve {
        virtual_token_reserves: c.virtual_token_reserves,
        virtual_sol_reserves: c.virtual_sol_reserves,
        real_token_reserves: c.real_token_reserves,
        real_sol_reserves: c.real_sol_reserves,
        complete: c.complete,
        has_creator: c.has_creator,
        creator_fee_bps: c.curve_creator_bps,
    };
    let config = buy::Config {
        tiers: &c.tiers,
        mint_supply: supply(c),
        creator_fee_configurable: c.creator_fee_configurable,
        buyback_bps: buyback_bps(c),
        vault_lamports: c.vault_lamports,
    };
    let recipients = buy_v2::Recipients { fee_recipient_ok: recipient_ok(c), buyback_ok: c.buyback_ok };
    let fill = if c.op == Op::Buy {
        buy_v2::buy_v2(&curve, &config, &recipients, c.amount, c.limit, &c.trailing)
    } else {
        buy_v2::buy_exact_quote_in_v2(&curve, &config, &recipients, c.amount, c.limit, &c.trailing)
    }?;
    Ok(Settled {
        tokens: fill.tokens,
        sol_amount: fill.sol_cost,
        protocol_bps: fill.protocol_bps,
        protocol_fee: fill.protocol_fee,
        creator_bps: fill.creator_bps,
        creator_fee: fill.creator_fee,
        buyback_fee: fill.buyback_fee,
        vault_credit: fill.vault_credit,
        user_delta: -(fill.sol_cost as i128 + fill.protocol_fee as i128 + fill.vault_credit as i128),
        virtual_token_reserves: fill.curve.virtual_token_reserves,
        virtual_sol_reserves: fill.curve.virtual_sol_reserves,
        real_token_reserves: fill.curve.real_token_reserves,
        real_sol_reserves: fill.curve.real_sol_reserves,
        completes: fill.curve.complete,
        holder_rewards_bps: if c.holder_reward { fill.creator_bps } else { 0 },
        holder_rewards: if c.holder_reward { fill.creator_fee } else { 0 },
        buyback_bps: buyback_bps(c),
    })
}

fn run_sell(c: &Case) -> Result<Settled, Stop> {
    let curve = sell::Curve {
        virtual_token_reserves: c.virtual_token_reserves,
        virtual_sol_reserves: c.virtual_sol_reserves,
        real_token_reserves: c.real_token_reserves,
        real_sol_reserves: c.real_sol_reserves,
        complete: c.complete,
        has_creator: c.has_creator,
        creator_fee_bps: c.curve_creator_bps,
    };
    let tiers: Vec<sell::Tier> = c
        .tiers
        .iter()
        .map(|t| sell::Tier { threshold: t.threshold, protocol_bps: t.protocol_bps, creator_bps: t.creator_bps })
        .collect();
    let config = sell::Config {
        tiers: &tiers,
        mint_supply: supply(c),
        creator_fee_configurable: c.creator_fee_configurable,
        buyback_bps: buyback_bps(c),
        vault_lamports: c.vault_lamports,
        user_tokens: c.user_tokens,
        remaining: [sell::Slot::CurveV2, sell::Slot::Buyback],
    };
    let recipients = sell_v2::Recipients { fee_recipient_ok: recipient_ok(c), buyback_ok: c.buyback_ok };
    let (fill, rent) = sell_v2::sell_v2(&curve, &config, &recipients, c.amount, c.limit)?;
    Ok(Settled {
        tokens: c.amount,
        sol_amount: fill.sol_output,
        protocol_bps: fill.protocol_bps,
        protocol_fee: fill.protocol_fee,
        creator_bps: fill.creator_bps,
        creator_fee: fill.creator_fee,
        buyback_fee: fill.buyback_fee,
        vault_credit: fill.creator_fee + fill.vault_top_up,
        user_delta: fill.user_output as i128 - fill.vault_top_up as i128 - rent as i128,
        virtual_token_reserves: fill.curve.virtual_token_reserves,
        virtual_sol_reserves: fill.curve.virtual_sol_reserves,
        real_token_reserves: fill.curve.real_token_reserves,
        real_sol_reserves: fill.curve.real_sol_reserves,
        completes: false,
        holder_rewards_bps: if c.holder_reward { fill.creator_bps } else { 0 },
        holder_rewards: if c.holder_reward { fill.creator_fee } else { 0 },
        buyback_bps: buyback_bps(c),
    })
}

pub fn run(c: &Case) -> Result<Settled, Stop> {
    if c.op == Op::Sell {
        run_sell(c)
    } else {
        run_buy(c)
    }
}
