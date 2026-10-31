//! Captured behavior of Pump legacy and v2 SOL trades when one key fills two
//! account slots: `Global.fee_recipient` or the buyback recipient naming the
//! buyer, the curve, the creator vault, each other, a program, or any other
//! account of the instruction, and the curve's own token account passed as
//! the buyer's. Pricing comes from `legacy_buy.rs` and `legacy_sell.rs`, which
//! the host declares beside this module, on a regular coin with a stored
//! user volume accumulator.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured Pump
//! Fees, SPL Token, and Associated Token programs by
//! `tests/test_trade_alias_captured.py`. Not linked into the SBF crate. This is
//! not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): which of the curve and vault
//! payments goes first (a recipient key cannot equal the buyer's vault here, so
//! both orders give the same answers), a curve holding less than its reserves,
//! the all-zero key as a recipient, token quotes, Mayhem, and cashback coins.

use crate::{legacy_buy as buy, legacy_sell as sell};

/// Anchor `ConstraintMut`: a program key cannot be writable in a transaction.
pub const CONSTRAINT_MUT: u32 = 2000;
/// SPL Token `OwnerMismatch`.
pub const TOKEN_OWNER_MISMATCH: u32 = 4;
/// System Program `ResultWithNegativeLamports`.
pub const SYSTEM_INSUFFICIENT_LAMPORTS: u32 = 1;
pub const TX_FEE: u64 = 5000;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    Panic,
    /// The SOL transfer credited an executable account it cannot change.
    ExternalAccountLamportSpend,
    /// The SOL transfer named the running program, which is read-only.
    PrivilegeEscalation,
    /// The sell moved lamports of the read-only program account.
    ReadonlyLamportChange,
    /// The event CPI saw lamports moved on its read-only signer.
    UnbalancedInstruction,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Op {
    Buy,
    BuyExact,
    Sell,
    BuyV2,
    BuyExactV2,
    SellV2,
}

impl Op {
    fn v2(self) -> bool {
        matches!(self, Op::BuyV2 | Op::BuyExactV2 | Op::SellV2)
    }

    fn sells(self) -> bool {
        matches!(self, Op::Sell | Op::SellV2)
    }
}

/// The account a recipient key names.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Party {
    /// The stored `fee_recipient`, on its own.
    Fee,
    /// The stored buyback recipient, on its own.
    Buyback,
    User,
    Curve,
    Vault,
    /// An ordinary account of the instruction, by slot. Slots other than the
    /// ones above behave alike.
    Plain(u8),
    TokenProgram,
    PumpProgram,
    EventAuthority,
}

pub struct Trade<'a> {
    pub op: Op,
    pub reserves: [u64; 4],
    pub supply: u64,
    pub complete: bool,
    pub tiers: &'a [(u128, u64, u64)],
    pub buyback_bps: u64,
    pub vault_lamports: u64,
    pub user_lamports: u64,
    pub user_tokens: u64,
    pub curve_tokens: u64,
    pub args: (u64, u64),
    pub fee: Party,
    pub buyback: Party,
    /// `associated_user` is the curve's own token account.
    pub buyer_is_curve_ata: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Settled {
    /// Net lamport change of each key, payment fee included.
    pub lamports: Vec<(Party, i128)>,
    pub user_tokens: u64,
    pub curve_tokens: u64,
    pub reserves: [u64; 4],
    pub complete: bool,
    pub sol_amount: u64,
    pub token_amount: u64,
    pub protocol_fee: u64,
    pub creator_fee: u64,
    pub buyback_fee: u64,
}

/// One priced trade before any key is compared.
struct Priced {
    /// Buy: paid to the curve. Sell: paid by the curve.
    sol: u64,
    tokens: u64,
    protocol_fee: u64,
    creator_fee: u64,
    buyback_fee: u64,
    /// Buy: creator fee plus rent. Sell: creator fee.
    vault_credit: u64,
    /// Sell: rent the seller adds.
    vault_top_up: u64,
    /// Sell: what the seller receives from the curve.
    user_output: u64,
    reserves: [u64; 4],
    complete: bool,
}

fn price(t: &Trade) -> Result<Priced, Stop> {
    let [vt, vs, rt, rs] = t.reserves;
    if t.op.sells() {
        let tiers: Vec<sell::Tier> = t
            .tiers
            .iter()
            .map(|&(threshold, protocol_bps, creator_bps)| sell::Tier { threshold, protocol_bps, creator_bps })
            .collect();
        let curve = sell::Curve {
            virtual_token_reserves: vt,
            virtual_sol_reserves: vs,
            real_token_reserves: rt,
            real_sol_reserves: rs,
            complete: t.complete,
            has_creator: true,
            creator_fee_bps: 0,
        };
        let config = sell::Config {
            tiers: &tiers,
            mint_supply: t.supply,
            creator_fee_configurable: false,
            buyback_bps: t.buyback_bps,
            vault_lamports: t.vault_lamports,
            user_tokens: t.user_tokens,
            remaining: [sell::Slot::CurveV2, sell::Slot::Buyback],
        };
        let fill = sell::sell(&curve, &config, t.args.0, t.args.1).map_err(|stop| match stop {
            sell::Stop::Code(code) => Stop::Code(code),
            sell::Stop::Panic => Stop::Panic,
        })?;
        let c = fill.curve;
        return Ok(Priced {
            sol: fill.sol_output,
            tokens: t.args.0,
            protocol_fee: fill.protocol_fee,
            creator_fee: fill.creator_fee,
            buyback_fee: fill.buyback_fee,
            vault_credit: fill.creator_fee + fill.vault_top_up,
            vault_top_up: fill.vault_top_up,
            user_output: fill.user_output,
            reserves: [c.virtual_token_reserves, c.virtual_sol_reserves, c.real_token_reserves, c.real_sol_reserves],
            complete: c.complete,
        });
    }
    let tiers: Vec<buy::Tier> = t
        .tiers
        .iter()
        .map(|&(threshold, protocol_bps, creator_bps)| buy::Tier { threshold, protocol_bps, creator_bps })
        .collect();
    let curve = buy::Curve {
        virtual_token_reserves: vt,
        virtual_sol_reserves: vs,
        real_token_reserves: rt,
        real_sol_reserves: rs,
        complete: t.complete,
        has_creator: true,
        creator_fee_bps: 0,
    };
    let config = buy::Config {
        tiers: &tiers,
        mint_supply: t.supply,
        creator_fee_configurable: false,
        buyback_bps: t.buyback_bps,
        vault_lamports: t.vault_lamports,
    };
    let fill = if matches!(t.op, Op::Buy | Op::BuyV2) {
        buy::buy(&curve, &config, t.args.0, t.args.1, b"")
    } else {
        buy::buy_exact_sol_in(&curve, &config, t.args.0, t.args.1, b"")
    }
    .map_err(|stop| match stop {
        buy::Stop::Code(code) => Stop::Code(code),
        buy::Stop::Panic => Stop::Panic,
    })?;
    let c = fill.curve;
    Ok(Priced {
        sol: fill.sol_cost,
        tokens: fill.tokens,
        protocol_fee: fill.protocol_fee,
        creator_fee: fill.creator_fee,
        buyback_fee: fill.buyback_fee,
        vault_credit: fill.vault_credit,
        vault_top_up: 0,
        user_output: 0,
        reserves: [c.virtual_token_reserves, c.virtual_sol_reserves, c.real_token_reserves, c.real_sol_reserves],
        complete: c.complete,
    })
}

/// The buyer's SOL transfers, in program order. Each runs through the System
/// Program, so a transfer from the buyer to the buyer moves nothing but still
/// needs the balance. Legacy buys pay the buyback before the fee, v2 after.
fn payments(t: &Trade, p: &Priced) -> [(Party, u64); 4] {
    let (first, second) = (Party::Curve, Party::Vault);
    let (fee, buyback) = (p.protocol_fee - p.buyback_fee, p.buyback_fee);
    if t.op.v2() {
        [(first, p.sol), (second, p.vault_credit), (t.fee, fee), (t.buyback, buyback)]
    } else {
        [(first, p.sol), (second, p.vault_credit), (t.buyback, buyback), (t.fee, fee)]
    }
}

/// The smallest balance that lets a buy finish; `None` when it does not price.
pub fn required_balance(t: &Trade) -> Option<u64> {
    if t.op.sells() {
        return None;
    }
    let p = price(t).ok()?;
    let mut need = 0u64;
    for (party, amount) in payments(t, &p).into_iter().rev() {
        if amount == 0 {
            continue;
        }
        need = if party == Party::User { need.max(amount) } else { need + amount };
    }
    Some(need + TX_FEE)
}

fn add(lamports: &mut Vec<(Party, i128)>, party: Party, amount: i128) {
    match lamports.iter_mut().find(|(p, _)| *p == party) {
        Some(entry) => entry.1 += amount,
        None => lamports.push((party, amount)),
    }
}

/// A program key cannot be writable: Anchor refuses it in the `fee_recipient`
/// slot, and in the v2 `buyback_fee_recipient` slot, ahead of every other stop.
/// The legacy buyback key is a remaining account, which Anchor does not check.
fn admitted(t: &Trade) -> Result<(), Stop> {
    if t.fee == Party::PumpProgram || (t.op.v2() && t.buyback == Party::PumpProgram) {
        return Err(Stop::Code(CONSTRAINT_MUT));
    }
    Ok(())
}

fn settle_buy(t: &Trade, p: &Priced, lamports: &mut Vec<(Party, i128)>) -> Result<(), Stop> {
    let mut balance = t.user_lamports - TX_FEE;
    add(lamports, Party::User, -(TX_FEE as i128));
    for (party, amount) in payments(t, p) {
        if amount == 0 {
            continue;
        }
        if balance < amount {
            return Err(Stop::Code(SYSTEM_INSUFFICIENT_LAMPORTS));
        }
        match party {
            Party::TokenProgram => return Err(Stop::ExternalAccountLamportSpend),
            Party::PumpProgram => return Err(Stop::PrivilegeEscalation),
            Party::User => {}
            other => {
                balance -= amount;
                add(lamports, Party::User, -(amount as i128));
                add(lamports, other, amount as i128);
            }
        }
    }
    Ok(())
}

/// A sell pays out of the curve by direct lamport writes, so programs can be
/// credited, and the event CPI that follows trips over read-only accounts.
fn settle_sell(t: &Trade, p: &Priced, lamports: &mut Vec<(Party, i128)>) -> Result<(), Stop> {
    let (fee, buyback) = (p.protocol_fee - p.buyback_fee, p.buyback_fee);
    if (t.fee == Party::EventAuthority && fee != 0) || (t.buyback == Party::EventAuthority && buyback != 0) {
        return Err(Stop::UnbalancedInstruction);
    }
    if t.buyback == Party::PumpProgram && buyback != 0 {
        return Err(Stop::ReadonlyLamportChange);
    }
    add(lamports, Party::User, -(TX_FEE as i128));
    add(lamports, Party::Curve, -(p.sol as i128));
    add(lamports, Party::User, p.user_output as i128 - p.vault_top_up as i128);
    add(lamports, Party::Vault, p.vault_credit as i128);
    add(lamports, t.fee, fee as i128);
    add(lamports, t.buyback, buyback as i128);
    Ok(())
}

pub fn trade(t: &Trade) -> Result<Settled, Stop> {
    admitted(t)?;
    let p = price(t)?;
    let mut lamports = Vec::new();
    if t.op.sells() {
        if t.buyer_is_curve_ata {
            return Err(Stop::Code(TOKEN_OWNER_MISMATCH));
        }
        settle_sell(t, &p, &mut lamports)?;
    } else {
        settle_buy(t, &p, &mut lamports)?;
    }
    lamports.retain(|(_, amount)| *amount != 0);
    let (user_tokens, curve_tokens) = if t.buyer_is_curve_ata {
        (t.user_tokens, t.curve_tokens)
    } else if t.op.sells() {
        (t.user_tokens - p.tokens, t.curve_tokens + p.tokens)
    } else {
        (t.user_tokens + p.tokens, t.curve_tokens - p.tokens)
    };
    Ok(Settled {
        lamports,
        user_tokens,
        curve_tokens,
        reserves: p.reserves,
        complete: p.complete,
        sol_amount: p.sol,
        token_amount: p.tokens,
        protocol_fee: p.protocol_fee,
        creator_fee: p.creator_fee,
        buyback_fee: p.buyback_fee,
    })
}
