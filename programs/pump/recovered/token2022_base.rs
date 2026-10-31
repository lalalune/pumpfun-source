//! Captured behavior of Pump's native trades on a Token-2022 base mint: legacy
//! `sell`, `buy` and `buy_exact_sol_in`, and `sell_v2`, `buy_v2` and
//! `buy_exact_quote_in_v2`, expressed on top of `legacy_sell.rs`, `legacy_buy.rs`,
//! `sell_v2.rs` and `buy_v2.rs`. Pricing, fees and reserves ignore the base
//! program: they stay nominal even when a `TransferFeeConfig` keeps part of the
//! tokens from reaching the destination. What differs is the base-account
//! admission and the outcome of the token transfer.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_token2022_base_captured.py`. Not linked into the
//! SBF crate. This is not a byte-identity claim. Unconfirmed (미확인, outside the
//! checked inputs): the recipient checks of the legacy instructions other than
//! the buyback slot of `sell`, Mayhem,
//! cashback and whitelist coins on this route, a base account whose owner
//! differs from the mint's, and a fee schedule whose two epochs differ.

use crate::buy_v2;
use crate::legacy_buy as buy;
use crate::legacy_sell as sell;
use crate::sell_v2;

/// Anchor `ConstraintAssociated`: the base account is not the ATA of its owner.
pub const CONSTRAINT_ASSOCIATED: u32 = 2009;
/// Anchor `ConstraintAssociatedTokenTokenProgram`: the base account is not owned
/// by the named token program.
pub const CONSTRAINT_ASSOCIATED_TOKEN_PROGRAM: u32 = 2023;
/// Token-2022 `NonTransferable`.
pub const NON_TRANSFERABLE: u32 = 37;
/// Token-2022 `MintPaused`.
pub const MINT_PAUSED: u32 = 67;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Family {
    Legacy,
    V2,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Op {
    Sell,
    Buy,
    /// `buy_exact_sol_in` or `buy_exact_quote_in_v2`.
    BuyExact,
}

/// SPL Token or Token-2022.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Program {
    Spl,
    Token2022,
}

/// The Token-2022 mint extension that reaches the transfer.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Extension {
    /// No extension, or one that does not change a transfer (metadata pointer,
    /// permanent delegate, an unset transfer hook, an unpaused mint).
    Inert,
    TransferFee { bps: u16, maximum: u64 },
    /// A hook program is set; these instructions pass no hook accounts.
    TransferHook,
    NonTransferable,
    Paused,
}

#[derive(Clone, Debug)]
pub struct Case {
    pub family: Family,
    pub op: Op,
    pub amount: u64,
    /// `min_sol_output`, `max_sol_cost`, or the minimum tokens out.
    pub limit: u64,
    pub trailing: Vec<u8>,
    pub virtual_token_reserves: u64,
    pub virtual_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub real_sol_reserves: u64,
    pub complete: bool,
    pub has_creator: bool,
    pub curve_creator_bps: u64,
    pub creator_fee_configurable: bool,
    pub mint_supply: u64,
    pub buyback_bps: u64,
    pub vault_lamports: u64,
    pub user_tokens: u64,
    pub tiers: Vec<buy::Tier>,
    pub recipient_ok: bool,
    pub buyback_ok: bool,
    /// Program that owns the mint and base accounts.
    pub owner: Program,
    /// Program named by the instruction.
    pub program: Program,
    /// Program the base account addresses are derived with.
    pub ata: Program,
    pub extension: Extension,
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
    pub buyback_bps: u64,
    /// Tokens withheld on the destination account.
    pub withheld: u64,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    Code(u32),
    Panic,
    /// The runtime's `MissingAccount`, raised on the token-program call.
    MissingAccount,
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

/// Anchor's base-account checks: these run after the arguments decode and
/// before every instruction guard.
fn admit_base(c: &Case) -> Result<(), Stop> {
    if c.owner != c.program {
        return Err(Stop::Code(CONSTRAINT_ASSOCIATED_TOKEN_PROGRAM));
    }
    if c.ata != c.program {
        return Err(Stop::Code(CONSTRAINT_ASSOCIATED));
    }
    Ok(())
}

/// Token-2022 fee on a transfer: the ceiling of `amount * bps / 10000`, capped
/// at the schedule's maximum.
fn transfer_fee(amount: u64, bps: u16, maximum: u64) -> u64 {
    let fee = (amount as u128 * bps as u128).div_ceil(10_000);
    fee.min(maximum as u128) as u64
}

/// The token transfer runs after every guard of the trade.
fn transfer(extension: Extension, tokens: u64) -> Result<u64, Stop> {
    match extension {
        Extension::Inert => Ok(0),
        Extension::TransferFee { bps, maximum } => Ok(transfer_fee(tokens, bps, maximum)),
        Extension::TransferHook => Err(Stop::MissingAccount),
        Extension::NonTransferable => Err(Stop::Code(NON_TRANSFERABLE)),
        Extension::Paused => Err(Stop::Code(MINT_PAUSED)),
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
        mint_supply: c.mint_supply,
        creator_fee_configurable: c.creator_fee_configurable,
        buyback_bps: c.buyback_bps,
        vault_lamports: c.vault_lamports,
    };
    let recipients = buy_v2::Recipients { fee_recipient_ok: c.recipient_ok, buyback_ok: c.buyback_ok };
    let fill = match (c.family, c.op) {
        (Family::Legacy, Op::Buy) => buy::buy(&curve, &config, c.amount, c.limit, &c.trailing),
        (Family::Legacy, _) => buy::buy_exact_sol_in(&curve, &config, c.amount, c.limit, &c.trailing),
        (Family::V2, Op::Buy) => buy_v2::buy_v2(&curve, &config, &recipients, c.amount, c.limit, &c.trailing),
        (Family::V2, _) => buy_v2::buy_exact_quote_in_v2(&curve, &config, &recipients, c.amount, c.limit, &c.trailing),
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
        buyback_bps: c.buyback_bps,
        withheld: transfer(c.extension, fill.tokens)?,
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
        mint_supply: c.mint_supply,
        creator_fee_configurable: c.creator_fee_configurable,
        buyback_bps: c.buyback_bps,
        vault_lamports: c.vault_lamports,
        user_tokens: c.user_tokens,
        remaining: [sell::Slot::CurveV2, if c.buyback_ok { sell::Slot::Buyback } else { sell::Slot::Other }],
    };
    let recipients = sell_v2::Recipients { fee_recipient_ok: c.recipient_ok, buyback_ok: c.buyback_ok };
    let fill = if c.family == Family::V2 {
        sell_v2::sell_v2(&curve, &config, &recipients, c.amount, c.limit)?.0
    } else {
        sell::sell(&curve, &config, c.amount, c.limit)?
    };
    Ok(Settled {
        tokens: c.amount,
        sol_amount: fill.sol_output,
        protocol_bps: fill.protocol_bps,
        protocol_fee: fill.protocol_fee,
        creator_bps: fill.creator_bps,
        creator_fee: fill.creator_fee,
        buyback_fee: fill.buyback_fee,
        vault_credit: fill.creator_fee + fill.vault_top_up,
        user_delta: fill.user_output as i128 - fill.vault_top_up as i128,
        virtual_token_reserves: fill.curve.virtual_token_reserves,
        virtual_sol_reserves: fill.curve.virtual_sol_reserves,
        real_token_reserves: fill.curve.real_token_reserves,
        real_sol_reserves: fill.curve.real_sol_reserves,
        completes: false,
        buyback_bps: c.buyback_bps,
        withheld: transfer(c.extension, c.amount)?,
    })
}

pub fn run(c: &Case) -> Result<Settled, Stop> {
    // The arguments decode before Anchor loads any account.
    if c.op != Op::Sell {
        match c.family {
            Family::Legacy => {
                buy::parse_options(&c.trailing)?;
            }
            Family::V2 => {
                buy_v2::parse_partial(&c.trailing)?;
            }
        }
    }
    admit_base(c)?;
    let trade = if c.op == Op::Sell { run_sell } else { run_buy };
    // The token transfer runs before the buyback split, so its failure comes
    // ahead of the panic a rate above 10,000 bps causes there, and before the
    // buyback slot check of legacy `sell`.
    trade(&Case {
        buyback_bps: c.buyback_bps.min(10_000),
        buyback_ok: c.buyback_ok || c.family == Family::Legacy,
        ..c.clone()
    })?;
    trade(c)
}
