//! Captured cashback routing of Pump `sell_v2`, `buy_v2`, and
//! `buy_exact_quote_in_v2` on a native SOL curve.
//!
//! `sell_v2.rs` and `buy_v2.rs` price a regular coin and pay the creator fee
//! into the creator vault. On a cashback coin the same fee is paid into the
//! user's volume accumulator instead, the vault is not topped up, and the
//! TradeEvent reports the fee as cashback. Pricing, slippage, and the
//! recipient checks are unchanged and come from those two models.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured Pump
//! Fees program by `tests/test_v2_native_cashback_captured.py`. Not linked
//! into the SBF crate. This is not a byte-identity claim. Mayhem,
//! holder-reward, whitelist, and token-quote curves are out of scope.

use crate::buy_v2::{self, Recipients as BuyRecipients};
use crate::legacy_buy::{self, Config as BuyConfig, Curve as BuyCurve, Tier as BuyTier};
use crate::legacy_sell::{self, Config as SellConfig, Curve as SellCurve, Slot, Tier as SellTier};
use crate::sell_v2::{self, Recipients as SellRecipients};

pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_RENT_EXEMPT: u32 = 2005;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
/// System program `AccountAlreadyInUse`: `init_if_needed` found data in a
/// system-owned accumulator.
pub const ACCOUNT_ALREADY_IN_USE: u32 = 0;
/// `Rent::minimum_balance(137)`, the UserVolumeAccumulator size.
pub const UVA_RENT: u64 = 1_844_400;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Op {
    Sell,
    Buy,
    Exact,
}

/// How the `user_volume_accumulator` account looks before the instruction.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Hold {
    /// No account. `init_if_needed` creates it and the user pays the full rent.
    Missing,
    /// System-owned, no data, already holding `lamports`.
    Funded(u64),
    /// Pump-owned with the right discriminator.
    Valid {
        lamports: u64,
        earned: u64,
    },
    Foreign,
    BadDiscriminator,
    /// The passed account is not the user's accumulator PDA.
    WrongSeeds,
    /// System-owned and already carrying data.
    SystemData,
}

pub struct Admission {
    pub hold: Hold,
    pub writable: bool,
    /// `Valid` only. `Zero` is overwritten with the signer; `Other` is left.
    pub prior_user_other: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    /// `record_cashback_earned` aborts with `Overflowing cashback earned`,
    /// or the fee tier list is empty.
    Panic,
    /// Creating a missing accumulator requires a writable account.
    Privilege,
    /// `is_cashback_coin` is not 0 or 1, so the curve account does not load.
    Borsh,
}

pub struct Settled {
    pub sol: u64,
    pub tokens: u64,
    pub protocol_bps: u64,
    pub protocol_fee: u64,
    pub creator_bps: u64,
    pub creator_fee: u64,
    pub buyback_fee: u64,
    /// Lamports the creator vault gains. Zero on a cashback coin.
    pub vault_delta: u64,
    /// Lamports the accumulator gains, rent included.
    pub uva_delta: u64,
    /// `cashback_earned` after a success.
    pub earned: u64,
    pub event_creator_bps: u64,
    pub event_creator_fee: u64,
    pub event_cashback_bps: u64,
    pub event_cashback: u64,
    /// TradeEvent volume snapshot. Sells store zeros; the buys store the
    /// accumulator's fields, which this path does not change.
    pub event_unclaimed: u64,
    pub event_claimed: u64,
    pub event_volume: u64,
    pub event_last: i64,
    pub virtual_token: u64,
    pub virtual_sol: u64,
    pub real_token: u64,
    pub real_sol: u64,
    pub complete: bool,
    /// Lamports the seller receives from the curve. Zero on the buys, where
    /// the user pays instead.
    pub user_output: u64,
    pub ix_name: &'static str,
    /// The accumulator's `user` field is the signer afterwards.
    pub user_is_signer: bool,
}

/// Rent the user pays to create the accumulator, or the admission error.
fn admit(a: &Admission) -> Result<u64, Stop> {
    match a.hold {
        // The seeds constraint is the address itself, so it loses to nothing
        // else that is wrong about this account.
        Hold::WrongSeeds => return Err(Stop::Code(CONSTRAINT_SEEDS)),
        Hold::Foreign => return Err(Stop::Code(ACCOUNT_OWNED_BY_WRONG_PROGRAM)),
        Hold::BadDiscriminator => return Err(Stop::Code(ACCOUNT_DISCRIMINATOR_MISMATCH)),
        Hold::SystemData => return Err(Stop::Code(ACCOUNT_ALREADY_IN_USE)),
        // An existing Pump account is loaded, and a short one fails rent
        // before the mut constraint.
        Hold::Valid { lamports, .. } if lamports < UVA_RENT => {
            return Err(Stop::Code(CONSTRAINT_RENT_EXEMPT));
        }
        Hold::Missing | Hold::Funded(_) if !a.writable => return Err(Stop::Privilege),
        Hold::Valid { .. } if !a.writable => return Err(Stop::Code(CONSTRAINT_MUT)),
        Hold::Missing => Ok(UVA_RENT),
        Hold::Funded(have) => Ok(UVA_RENT.saturating_sub(have)),
        Hold::Valid { .. } => Ok(0),
    }
}

fn earned_before(hold: Hold) -> u64 {
    match hold {
        Hold::Valid { earned, .. } => earned,
        _ => 0,
    }
}

/// Where the priced creator fee goes, and the four TradeEvent fee fields.
/// A cashback coin keeps the priced bps on `cashback_fee_basis_points` even
/// when the fee itself is zero, and it never tops the creator vault up.
fn settle_route(
    cashback: bool,
    vault_delta: u64,
    creator_bps: u64,
    creator_fee: u64,
    earned: u64,
) -> Result<(u64, u64, u64, u64, u64, u64, u64), Stop> {
    let earned_after = if cashback && creator_fee > 0 {
        earned.checked_add(creator_fee).ok_or(Stop::Panic)?
    } else {
        earned
    };
    let fee_to_uva = if cashback { creator_fee } else { 0 };
    let vault_delta = if cashback { 0 } else { vault_delta };
    let event_creator_bps = if cashback { 0 } else { creator_bps };
    let event_creator_fee = if cashback { 0 } else { creator_fee };
    let event_cashback_bps = if cashback { creator_bps } else { 0 };
    let event_cashback = if cashback { creator_fee } else { 0 };
    Ok((
        vault_delta,
        fee_to_uva,
        earned_after,
        event_creator_bps,
        event_creator_fee,
        event_cashback_bps,
        event_cashback,
    ))
}

pub struct Trade<'a> {
    pub op: Op,
    /// 0 or 1. Any other byte is a curve decode failure.
    pub cashback: u8,
    pub admission: Admission,
    /// Volume snapshot already stored on a valid accumulator. Sells do not
    /// copy it into the event.
    pub unclaimed: u64,
    pub claimed: u64,
    pub volume: u64,
    pub last: i64,
    pub virtual_token: u64,
    pub virtual_sol: u64,
    pub real_token: u64,
    pub real_sol: u64,
    pub complete: bool,
    pub has_creator: bool,
    pub creator_bps: u64,
    pub supply: u64,
    pub configurable: bool,
    pub buyback_bps: u64,
    pub vault_lamports: u64,
    pub user_tokens: u64,
    pub fee_recipient_ok: bool,
    pub buyback_ok: bool,
    pub amount: u64,
    pub limit: u64,
    pub trailing: &'a [u8],
    pub tiers: &'a [(u128, u64, u64)],
}

pub fn execute(t: &Trade) -> Result<Settled, Stop> {
    if t.cashback > 1 {
        return Err(Stop::Borsh);
    }
    let rent = admit(&t.admission)?;
    let cashback = t.cashback == 1;
    let user_is_signer =
        !matches!(t.admission.hold, Hold::Valid { .. } if t.admission.prior_user_other);
    let earned = earned_before(t.admission.hold);
    // Sells hardcode a zero volume snapshot. The buys copy the accumulator,
    // which is still zero when this instruction has just created it.
    let stored = matches!(t.admission.hold, Hold::Valid { .. });
    let (snapshot_unclaimed, snapshot_claimed, snapshot_volume, snapshot_last) =
        if t.op == Op::Sell || !stored {
            (0, 0, 0, 0)
        } else {
            (t.unclaimed, t.claimed, t.volume, t.last)
        };
    match t.op {
        Op::Sell => {
            let curve = SellCurve {
                virtual_token_reserves: t.virtual_token,
                virtual_sol_reserves: t.virtual_sol,
                real_token_reserves: t.real_token,
                real_sol_reserves: t.real_sol,
                complete: t.complete,
                has_creator: t.has_creator,
                creator_fee_bps: t.creator_bps,
            };
            let tiers: Vec<SellTier> = t
                .tiers
                .iter()
                .map(|(threshold, protocol, creator)| SellTier {
                    threshold: *threshold,
                    protocol_bps: *protocol,
                    creator_bps: *creator,
                })
                .collect();
            let config = SellConfig {
                tiers: &tiers,
                mint_supply: t.supply,
                creator_fee_configurable: t.configurable,
                buyback_bps: t.buyback_bps,
                vault_lamports: t.vault_lamports,
                user_tokens: t.user_tokens,
                remaining: [Slot::Absent, Slot::Absent],
            };
            let recipients = SellRecipients {
                fee_recipient_ok: t.fee_recipient_ok,
                buyback_ok: t.buyback_ok,
            };
            let (fill, _) = sell_v2::sell_v2(&curve, &config, &recipients, t.amount, t.limit)
                .map_err(|e| match e {
                    legacy_sell::Stop::Code(code) => Stop::Code(code),
                    legacy_sell::Stop::Panic => Stop::Panic,
                })?;
            let vault_delta = fill.vault_top_up + fill.creator_fee;
            let (
                vault_delta,
                fee_to_uva,
                earned,
                event_creator_bps,
                event_creator_fee,
                event_cashback_bps,
                event_cashback,
            ) = settle_route(
                cashback,
                vault_delta,
                fill.creator_bps,
                fill.creator_fee,
                earned,
            )?;
            Ok(Settled {
                sol: fill.sol_output,
                tokens: t.amount,
                protocol_bps: fill.protocol_bps,
                protocol_fee: fill.protocol_fee,
                creator_bps: fill.creator_bps,
                creator_fee: fill.creator_fee,
                buyback_fee: fill.buyback_fee,
                vault_delta,
                uva_delta: rent + fee_to_uva,
                earned,
                event_creator_bps,
                event_creator_fee,
                event_cashback_bps,
                event_cashback,
                event_unclaimed: snapshot_unclaimed,
                event_claimed: snapshot_claimed,
                event_volume: snapshot_volume,
                event_last: snapshot_last,
                virtual_token: fill.curve.virtual_token_reserves,
                virtual_sol: fill.curve.virtual_sol_reserves,
                real_token: fill.curve.real_token_reserves,
                real_sol: fill.curve.real_sol_reserves,
                complete: fill.curve.complete,
                user_output: fill.user_output,
                ix_name: "sell",
                user_is_signer,
            })
        }
        Op::Buy | Op::Exact => {
            let curve = BuyCurve {
                virtual_token_reserves: t.virtual_token,
                virtual_sol_reserves: t.virtual_sol,
                real_token_reserves: t.real_token,
                real_sol_reserves: t.real_sol,
                complete: t.complete,
                has_creator: t.has_creator,
                creator_fee_bps: t.creator_bps,
            };
            let tiers: Vec<BuyTier> = t
                .tiers
                .iter()
                .map(|(threshold, protocol, creator)| BuyTier {
                    threshold: *threshold,
                    protocol_bps: *protocol,
                    creator_bps: *creator,
                })
                .collect();
            let config = BuyConfig {
                tiers: &tiers,
                mint_supply: t.supply,
                creator_fee_configurable: t.configurable,
                buyback_bps: t.buyback_bps,
                vault_lamports: t.vault_lamports,
            };
            let recipients = BuyRecipients {
                fee_recipient_ok: t.fee_recipient_ok,
                buyback_ok: t.buyback_ok,
            };
            let fill = match t.op {
                Op::Buy => {
                    buy_v2::buy_v2(&curve, &config, &recipients, t.amount, t.limit, t.trailing)
                }
                Op::Exact => buy_v2::buy_exact_quote_in_v2(
                    &curve,
                    &config,
                    &recipients,
                    t.amount,
                    t.limit,
                    t.trailing,
                ),
                Op::Sell => unreachable!(),
            }
            .map_err(|e| match e {
                legacy_buy::Stop::Code(code) => Stop::Code(code),
                legacy_buy::Stop::Panic => Stop::Panic,
            })?;
            let (
                vault_delta,
                fee_to_uva,
                earned,
                event_creator_bps,
                event_creator_fee,
                event_cashback_bps,
                event_cashback,
            ) = settle_route(
                cashback,
                fill.vault_credit,
                fill.creator_bps,
                fill.creator_fee,
                earned,
            )?;
            Ok(Settled {
                sol: fill.sol_cost,
                tokens: fill.tokens,
                protocol_bps: fill.protocol_bps,
                protocol_fee: fill.protocol_fee,
                creator_bps: fill.creator_bps,
                creator_fee: fill.creator_fee,
                buyback_fee: fill.buyback_fee,
                vault_delta,
                uva_delta: rent + fee_to_uva,
                earned,
                event_creator_bps,
                event_creator_fee,
                event_cashback_bps,
                event_cashback,
                event_unclaimed: snapshot_unclaimed,
                event_claimed: snapshot_claimed,
                event_volume: snapshot_volume,
                event_last: snapshot_last,
                virtual_token: fill.curve.virtual_token_reserves,
                virtual_sol: fill.curve.virtual_sol_reserves,
                real_token: fill.curve.real_token_reserves,
                real_sol: fill.curve.real_sol_reserves,
                complete: fill.curve.complete,
                user_output: 0,
                ix_name: if t.op == Op::Buy {
                    "buy"
                } else {
                    "buy_exact_quote_in"
                },
                user_is_signer,
            })
        }
    }
}
