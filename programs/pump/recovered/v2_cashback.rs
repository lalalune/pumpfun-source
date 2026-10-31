//! Captured accounting of Pump `sell_v2`, `buy_v2` and `buy_exact_quote_in_v2`
//! on the native cashback coins that `sell_v2.rs` and `buy_v2.rs` leave out,
//! expressed on top of those two models. A cashback coin sends its creator fee
//! to the user's `user_volume_accumulator` instead of the creator vault, with
//! no vault rent top-up, and reports it in the TradeEvent cashback fields. The
//! accumulator is created or topped up for every coin; a stored accumulator must
//! be rent exempt. Mayhem and holder-reward flags combine with this route.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_v2_cashback_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim. Unconfirmed (미확인, outside the
//! checked inputs): the whitelist PDA user and an accumulator whose lamports
//! leave u64.

use crate::buy_v2;
use crate::legacy_buy as buy;
use crate::legacy_sell as sell;
use crate::sell_v2;

/// Anchor `ConstraintRentExempt`.
pub const CONSTRAINT_RENT_EXEMPT: u32 = 2005;
/// Anchor `AccountDiscriminatorMismatch`.
pub const ACCOUNT_DISCRIMINATOR_MISMATCH: u32 = 3002;
/// Anchor `AccountOwnedByWrongProgram`.
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
/// `Rent::minimum_balance(137)`, the `UserVolumeAccumulator` size.
pub const UVA_RENT_MINIMUM: u64 = sell_v2::USER_VOLUME_ACCUMULATOR_RENT;

/// State of the user's `user_volume_accumulator` PDA before the trade.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Uva {
    Missing,
    /// System-owned, no data, holding some lamports.
    Funded(u64),
    /// Pump-owned with the right discriminator.
    Valid { lamports: u64, cashback_earned: u64 },
    ForeignOwner,
    BadDiscriminator,
}

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
    pub cashback: bool,
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
    pub uva: Uva,
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
    pub cashback_bps: u64,
    pub cashback: u64,
    pub buyback_fee: u64,
    /// Lamports the creator vault receives, including any rent top-up.
    pub vault_credit: u64,
    /// Lamports the accumulator receives: its rent shortfall plus any cashback.
    pub uva_credit: u64,
    /// `cashback_earned` after the trade.
    pub earned: u64,
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
    c.recipient == if c.mayhem { Recipient::Reserved } else { Recipient::Regular }
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

/// A cashback coin never reads the vault, so the shared pricing sees a funded
/// one and adds no top-up.
fn vault_lamports(c: &Case) -> u64 {
    if c.cashback {
        u64::MAX
    } else {
        c.vault_lamports
    }
}

/// Anchor's account checks: these run after the arguments decode and before
/// every instruction guard.
fn admit_accumulator(uva: Uva) -> Result<(), Stop> {
    match uva {
        Uva::ForeignOwner => Err(Stop::Code(ACCOUNT_OWNED_BY_WRONG_PROGRAM)),
        Uva::BadDiscriminator => Err(Stop::Code(ACCOUNT_DISCRIMINATOR_MISMATCH)),
        Uva::Valid { lamports, .. } if lamports < UVA_RENT_MINIMUM => Err(Stop::Code(CONSTRAINT_RENT_EXEMPT)),
        _ => Ok(()),
    }
}

/// Lamports the user pays to bring an unset accumulator to its rent minimum.
fn rent_shortfall(uva: Uva) -> u64 {
    match uva {
        Uva::Missing => UVA_RENT_MINIMUM,
        Uva::Funded(lamports) => UVA_RENT_MINIMUM.saturating_sub(lamports),
        _ => 0,
    }
}

fn earned_before(uva: Uva) -> u64 {
    match uva {
        Uva::Valid { cashback_earned, .. } => cashback_earned,
        _ => 0,
    }
}

/// Moves the creator fee to the accumulator on a cashback coin. A
/// `cashback_earned` that would leave u64 aborts the program rather than
/// failing with the 6024 legacy `buy` and `sell` give.
fn route(c: &Case, s: &mut Settled) -> Result<(), Stop> {
    let rent = rent_shortfall(c.uva);
    s.earned = earned_before(c.uva);
    s.uva_credit = rent;
    if c.cashback {
        s.earned = s.earned.checked_add(s.creator_fee).ok_or(Stop::Panic)?;
        s.uva_credit += s.creator_fee;
        s.cashback_bps = s.creator_bps;
        s.cashback = s.creator_fee;
        s.user_delta -= s.creator_fee as i128;
        s.creator_bps = 0;
        s.creator_fee = 0;
        s.vault_credit = 0;
    }
    s.user_delta -= rent as i128;
    Ok(())
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
        vault_lamports: vault_lamports(c),
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
        cashback_bps: 0,
        cashback: 0,
        buyback_fee: fill.buyback_fee,
        vault_credit: fill.vault_credit,
        uva_credit: 0,
        earned: 0,
        user_delta: -(fill.sol_cost as i128 + fill.protocol_fee as i128 + fill.vault_credit as i128)
            + if c.cashback { fill.creator_fee as i128 } else { 0 },
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
        vault_lamports: vault_lamports(c),
        user_tokens: c.user_tokens,
        remaining: [sell::Slot::CurveV2, sell::Slot::Buyback],
    };
    let recipients = sell_v2::Recipients { fee_recipient_ok: recipient_ok(c), buyback_ok: c.buyback_ok };
    // `sell_v2.rs` always charges the accumulator rent; this model charges the
    // shortfall in `route`, so its rent result is dropped here.
    let (fill, _) = sell_v2::sell_v2(&curve, &config, &recipients, c.amount, c.limit)?;
    Ok(Settled {
        tokens: c.amount,
        sol_amount: fill.sol_output,
        protocol_bps: fill.protocol_bps,
        protocol_fee: fill.protocol_fee,
        creator_bps: fill.creator_bps,
        creator_fee: fill.creator_fee,
        cashback_bps: 0,
        cashback: 0,
        buyback_fee: fill.buyback_fee,
        vault_credit: fill.creator_fee + fill.vault_top_up,
        uva_credit: 0,
        earned: 0,
        user_delta: fill.user_output as i128 - fill.vault_top_up as i128 + if c.cashback { fill.creator_fee as i128 } else { 0 },
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
    // The arguments decode before Anchor loads any account.
    if c.op != Op::Sell {
        buy_v2::parse_partial(&c.trailing)?;
    }
    admit_accumulator(c.uva)?;
    let mut settled = if c.op == Op::Sell { run_sell(c) } else { run_buy(c) }?;
    route(c, &mut settled)?;
    Ok(settled)
}
