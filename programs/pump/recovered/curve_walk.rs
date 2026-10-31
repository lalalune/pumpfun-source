//! One bonding curve carried through `buy`, `buy_exact_sol_in`, `sell` and
//! `collect_creator_fee`, each step starting from what the last one left.
//!
//! `legacy_buy.rs`, `legacy_sell.rs` and `creator_fee_collect.rs` price one
//! call from a given state. This thin model adds only what links the calls:
//! the balances each step hands to the next, the transaction fee (a failed
//! step still pays it and changes nothing else) and the fee tier a moving
//! market cap selects. Checked against the captured Pump program by
//! `tests/test_curve_walk_captured.py` on the walks listed there; that is
//! matching behaviour on those inputs, not a byte-identity claim.

use crate::creator_fee_collect::{self, Collect, Quote};
use crate::legacy_buy;
use crate::legacy_sell;

pub const TX_FEE: u64 = 5_000;

/// What stays fixed for a whole walk.
#[derive(Clone, Debug)]
pub struct Setup {
    pub has_creator: bool,
    pub creator_fee_bps: u64,
    pub mint_supply: u64,
    pub creator_fee_configurable: bool,
    pub buyback_bps: u64,
    /// `(threshold, protocol_bps, creator_bps)`.
    pub tiers: Vec<(u128, u64, u64)>,
}

/// What each step hands to the next.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct State {
    pub virtual_token_reserves: u64,
    pub virtual_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub real_sol_reserves: u64,
    pub complete: bool,
    pub user_tokens: u64,
    pub curve_tokens: u64,
    pub user_lamports: u64,
    pub curve_lamports: u64,
    pub recipient_lamports: u64,
    pub buyback_lamports: u64,
    pub vault_lamports: u64,
    pub creator_lamports: u64,
}

#[derive(Clone, Debug)]
pub enum Op {
    Buy { amount: u64, max_sol_cost: u64, trailing: Vec<u8> },
    ExactSolIn { spendable: u64, min_tokens: u64, trailing: Vec<u8> },
    Sell { amount: u64, min_sol_output: u64 },
    Collect,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    Panic,
}

/// The `TradeEvent` amounts of a step, or `None` for a step without one.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Trade {
    pub sol_amount: u64,
    pub token_amount: u64,
    pub is_buy: bool,
    pub fee_bps: u64,
    pub fee: u64,
    pub creator_bps: u64,
    pub creator_fee: u64,
    pub track_volume: bool,
    pub buyback_fee: u64,
}

fn buy_stop(stop: legacy_buy::Stop) -> Stop {
    match stop {
        legacy_buy::Stop::Code(code) => Stop::Code(code),
        legacy_buy::Stop::Panic => Stop::Panic,
    }
}

fn sell_stop(stop: legacy_sell::Stop) -> Stop {
    match stop {
        legacy_sell::Stop::Code(code) => Stop::Code(code),
        legacy_sell::Stop::Panic => Stop::Panic,
    }
}

fn step_buy(state: &mut State, setup: &Setup, op: &Op) -> Result<Option<Trade>, Stop> {
    let curve = legacy_buy::Curve {
        virtual_token_reserves: state.virtual_token_reserves,
        virtual_sol_reserves: state.virtual_sol_reserves,
        real_token_reserves: state.real_token_reserves,
        real_sol_reserves: state.real_sol_reserves,
        complete: state.complete,
        has_creator: setup.has_creator,
        creator_fee_bps: setup.creator_fee_bps,
    };
    let tiers: Vec<legacy_buy::Tier> = setup
        .tiers
        .iter()
        .map(|t| legacy_buy::Tier { threshold: t.0, protocol_bps: t.1, creator_bps: t.2 })
        .collect();
    let config = legacy_buy::Config {
        tiers: &tiers,
        mint_supply: setup.mint_supply,
        creator_fee_configurable: setup.creator_fee_configurable,
        buyback_bps: setup.buyback_bps,
        vault_lamports: state.vault_lamports,
    };
    let (fill, trailing) = match op {
        Op::Buy { amount, max_sol_cost, trailing } => {
            (legacy_buy::buy(&curve, &config, *amount, *max_sol_cost, trailing), trailing)
        }
        Op::ExactSolIn { spendable, min_tokens, trailing } => {
            (legacy_buy::buy_exact_sol_in(&curve, &config, *spendable, *min_tokens, trailing), trailing)
        }
        _ => unreachable!(),
    };
    let fill = fill.map_err(buy_stop)?;
    let (track_volume, _) = legacy_buy::parse_options(trailing).map_err(buy_stop)?;
    state.virtual_token_reserves = fill.curve.virtual_token_reserves;
    state.virtual_sol_reserves = fill.curve.virtual_sol_reserves;
    state.real_token_reserves = fill.curve.real_token_reserves;
    state.real_sol_reserves = fill.curve.real_sol_reserves;
    state.complete = fill.curve.complete;
    state.user_tokens += fill.tokens;
    state.curve_tokens -= fill.tokens;
    state.user_lamports -= fill.sol_cost + fill.protocol_fee + fill.vault_credit;
    state.curve_lamports += fill.sol_cost;
    state.recipient_lamports += fill.protocol_fee - fill.buyback_fee;
    state.buyback_lamports += fill.buyback_fee;
    state.vault_lamports += fill.vault_credit;
    Ok(Some(Trade {
        sol_amount: fill.sol_cost,
        token_amount: fill.tokens,
        is_buy: true,
        fee_bps: fill.protocol_bps,
        fee: fill.protocol_fee,
        creator_bps: fill.creator_bps,
        creator_fee: fill.creator_fee,
        track_volume,
        buyback_fee: fill.buyback_fee,
    }))
}

fn step_sell(state: &mut State, setup: &Setup, amount: u64, min_sol_output: u64) -> Result<Option<Trade>, Stop> {
    let curve = legacy_sell::Curve {
        virtual_token_reserves: state.virtual_token_reserves,
        virtual_sol_reserves: state.virtual_sol_reserves,
        real_token_reserves: state.real_token_reserves,
        real_sol_reserves: state.real_sol_reserves,
        complete: state.complete,
        has_creator: setup.has_creator,
        creator_fee_bps: setup.creator_fee_bps,
    };
    let tiers: Vec<legacy_sell::Tier> = setup
        .tiers
        .iter()
        .map(|t| legacy_sell::Tier { threshold: t.0, protocol_bps: t.1, creator_bps: t.2 })
        .collect();
    let config = legacy_sell::Config {
        tiers: &tiers,
        mint_supply: setup.mint_supply,
        creator_fee_configurable: setup.creator_fee_configurable,
        buyback_bps: setup.buyback_bps,
        vault_lamports: state.vault_lamports,
        user_tokens: state.user_tokens,
        remaining: [legacy_sell::Slot::CurveV2, legacy_sell::Slot::Buyback],
    };
    let fill = legacy_sell::sell(&curve, &config, amount, min_sol_output).map_err(sell_stop)?;
    state.virtual_token_reserves = fill.curve.virtual_token_reserves;
    state.virtual_sol_reserves = fill.curve.virtual_sol_reserves;
    state.real_token_reserves = fill.curve.real_token_reserves;
    state.real_sol_reserves = fill.curve.real_sol_reserves;
    state.user_tokens -= amount;
    state.curve_tokens += amount;
    state.user_lamports = state.user_lamports + fill.user_output - fill.vault_top_up;
    state.curve_lamports -= fill.sol_output;
    state.recipient_lamports += fill.protocol_fee - fill.buyback_fee;
    state.buyback_lamports += fill.buyback_fee;
    state.vault_lamports += fill.vault_top_up + fill.creator_fee;
    Ok(Some(Trade {
        sol_amount: fill.sol_output,
        token_amount: amount,
        is_buy: false,
        fee_bps: fill.protocol_bps,
        fee: fill.protocol_fee,
        creator_bps: fill.creator_bps,
        creator_fee: fill.creator_fee,
        track_volume: false,
        buyback_fee: fill.buyback_fee,
    }))
}

fn step_collect(state: &mut State) -> Result<Option<Trade>, Stop> {
    let collected = creator_fee_collect::collect(&Collect {
        creator_owned_by_fees: false,
        creator_executable: false,
        creator_lamports: state.creator_lamports,
        creator_data_len: 0,
        vault_lamports: state.vault_lamports,
        quote: Quote::Native,
    })
    .map_err(|_| Stop::Panic)?;
    state.vault_lamports -= collected.lamports;
    state.creator_lamports += collected.lamports;
    Ok(None)
}

/// Runs one step. On a stop only the transaction fee leaves `state`.
pub fn step(state: &mut State, setup: &Setup, op: &Op) -> Result<Option<Trade>, Stop> {
    state.user_lamports -= TX_FEE;
    match op {
        Op::Buy { .. } | Op::ExactSolIn { .. } => step_buy(state, setup, op),
        Op::Sell { amount, min_sol_output } => step_sell(state, setup, *amount, *min_sol_output),
        Op::Collect => step_collect(state),
    }
}
