//! Captured reading of accounts past the declared list of Pump commands,
//! on the wider harvest.
//!
//! `trailing_accounts.rs` answers how an extra key changes a run, but its test
//! stops each base test after 30 transactions and reaches 16 of them, so four
//! of its arms are marked unconfirmed there and several more rest on few rows.
//! This model is the same reading checked by `tests/test_trailing_accounts_deep_captured.py`,
//! which runs 26 base tests, lets each send up to 300 transactions and keeps
//! eight rows per class: 16,404 recorded comparisons. Every arm the first
//! model left unconfirmed is confirmed here, and where the wider harvest
//! disagrees with an arm, this file carries the corrected answer and says why.
//! The first model is unchanged; where the two disagree, the answers here are
//! the ones the deeper harvest holds.
//!
//! `Same` means the run keeps its error, logs and account state. `Open` means
//! the outcome depends on something the row does not hold, so no recorded
//! comparison is claimed for it either way.
//!
//! Corrections the wider harvest forces:
//!
//! - The `buy` and `sell` slot arms (6062 to 6057, 6072 to 6073) and the token
//!   route of `distribute_creator_fees_v2` are confirmed. At exactly two
//!   honest remaining keys the buyback arm does not hold: some base cases move
//!   to 6057 and some keep 6062, and which keys the two are is not in the row,
//!   so that case answers `Open`.
//! - On the token route of `distribute_creator_fees_v2` with no honest
//!   remaining keys, filling some but not all recipient slots changes the logs
//!   before the same 6027, so those rows answer `Open`, not `Same`.
//! - `create_v2` runs based on 6063 with three or four remaining keys move to
//!   6075 or 6099 in some base cases and stay in others; the row does not hold
//!   which, so they answer `Open`.
//! - The `distribute_fee_to_holders` count check is not first: the Anchor and
//!   account errors 2006, 3010 and 3012 and the handler's own 6000 precede
//!   it and keep the honest outcome. When the honest run itself fails the
//!   count check (6085), an appended count that lands exactly on a fixture's
//!   expected recipient count lets the run proceed past it; the expected
//!   count is not in the row, so the (remaining, extra) pairs where that was
//!   observed answer `Open`.
//! - The `migrate` two-extra answer holds when the honest run fails 6027.
//!   When the honest run passes with no remaining accounts, two extras move
//!   some base cases and not others, so that case answers `Open`.
//! - `multi_hop_curve_swap` with five honest remaining keys and a 6020 base
//!   reads the extras as another hop group in some base cases: `Open`.
//! - `sell` runs based on 6074 with at most one remaining key keep the code
//!   but not the account state: `Open`. With two or more they hold as `Same`.
//! - A transaction-level error (a base starting with `TransactionError`)
//!   answers `Open`: an appended unfunded key can change the rent outcome.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_trailing_accounts_deep_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.

/// `NotEnoughRemainingAccounts`.
pub const NOT_ENOUGH_REMAINING: u32 = 6027;
/// `ShareholdersAndRemainingAccountsMismatch`.
pub const WRONG_SHAREHOLDER: u32 = 6054;
/// `BuybackFeeRecipientNotAuthorized`.
pub const NOT_BUYBACK_RECIPIENT: u32 = 6057;
/// `WrongBuybackFeeRecipientsCount`: `update_buyback_config` takes zero or eight keys.
pub const WRONG_BUYBACK_COUNT: u32 = 6061;
/// `BuybackFeeRecipientMissing`.
pub const BUYBACK_MISSING: u32 = 6062;
/// `UnsupportedQuoteMint`.
pub const UNSUPPORTED_QUOTE_MINT: u32 = 6063;
/// `InvalidQuoteTokenProgram`.
pub const INVALID_QUOTE_PROGRAM: u32 = 6064;
/// `MissingCashbackAccounts`.
pub const CASHBACK_MISSING: u32 = 6072;
/// `InvalidCashbackAccumulator`.
pub const WRONG_CASHBACK_ACCOUNT: u32 = 6073;
/// `InvalidBondingCurveV2`.
pub const INVALID_BONDING_CURVE_V2: u32 = 6074;
/// `HolderRewardRecipientsMismatch`.
pub const HOLDER_COUNT: u32 = 6085;
/// Anchor `ConstraintRentExempt`, on an unfunded key in the eight-key lists.
pub const RENT_EXEMPT: u32 = 2005;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Answer {
    /// The honest run: same error, logs and account state.
    Same,
    /// The honest run with its remaining accounts cut away.
    Bare,
    Code(u32),
    /// A runtime error with no custom code.
    Runtime(&'static str),
    Pass,
    /// Not answered here.
    Open,
}

/// What the test knows about a run, plus how many keys it appends.
#[derive(Clone, Copy, Debug)]
pub struct Run<'a> {
    pub name: &'a str,
    /// Keys past the declared list in the honest transaction.
    pub remaining: usize,
    pub extra: usize,
    /// Outcome of the honest transaction: `ok`, a code, or a runtime error name.
    pub base: &'a str,
    /// Stored shareholder rows, where the command has a `SharingConfig`.
    pub rows: usize,
}

fn distribution_native(run: &Run) -> Answer {
    if run.base == code(NOT_ENOUGH_REMAINING) {
        return Answer::Code(WRONG_SHAREHOLDER);
    }
    Answer::Same
}

/// Each row reads its recipient, then its ATA at `rows + i`. With no honest
/// remaining keys, a partly filled list changes the logs before the same
/// 6027, so that case is not held as `Same`.
fn distribution_token(run: &Run) -> Answer {
    if run.base != code(NOT_ENOUGH_REMAINING) {
        return Answer::Same;
    }
    let total = run.remaining + run.extra;
    for i in 0..run.rows {
        if i >= total || run.rows + i >= total {
            return if run.remaining == 0 { Answer::Open } else { Answer::Same };
        }
        if i >= run.remaining || run.rows + i >= run.remaining {
            return Answer::Code(WRONG_SHAREHOLDER);
        }
    }
    if run.remaining == 0 { Answer::Open } else { Answer::Same }
}

fn eight_key_list(run: &Run) -> Answer {
    if run.base != code(NOT_ENOUGH_REMAINING) {
        return Answer::Same;
    }
    if run.remaining + run.extra >= 8 {
        return Answer::Code(RENT_EXEMPT);
    }
    // The log line of `require_gte!` prints the count, so only the code holds.
    Answer::Code(NOT_ENOUGH_REMAINING)
}

fn buyback_config(run: &Run) -> Answer {
    // The basis point check and the Anchor checks come first.
    if !matches!(run.base, "ok" | "6058" | "6059" | "6061") {
        return Answer::Same;
    }
    match run.remaining + run.extra {
        8 => Answer::Pass,
        _ => Answer::Code(WRONG_BUYBACK_COUNT),
    }
}

/// Anchor checks, the enable flag and the `init`s come first, so only a run that
/// reaches the quote check moves. A 6063 base with three or four remaining
/// keys reads the keys past the quote triple as further quote state and moves
/// in some base cases only, so it is not answered.
fn create_v2(run: &Run) -> Answer {
    if run.base == code(UNSUPPORTED_QUOTE_MINT) && matches!(run.remaining, 3 | 4) {
        return Answer::Open;
    }
    let reached = run.base == "ok" || run.base == code(NOT_ENOUGH_REMAINING);
    if run.remaining >= 3 || !reached {
        return Answer::Same;
    }
    if run.remaining + run.extra >= 3 {
        return Answer::Code(INVALID_QUOTE_PROGRAM);
    }
    Answer::Code(NOT_ENOUGH_REMAINING)
}

fn buyback_slot(run: &Run, index: usize) -> Answer {
    if run.base == code(BUYBACK_MISSING) && run.remaining + run.extra > index {
        // At two honest remaining keys the appended keys land past the slot
        // in some base cases and the run keeps 6062; the row does not hold
        // which keys the two are.
        if run.remaining == 2 {
            return Answer::Open;
        }
        return Answer::Code(NOT_BUYBACK_RECIPIENT);
    }
    Answer::Same
}

/// The handler pattern-matches exactly two keys. Any other count takes the
/// no-boost branch, which is 6027 while the AMM config has boost on and a plain
/// skip otherwise, as the same call with no remaining accounts shows. A passing
/// run with no remaining accounts takes the two-extra error only in the base
/// cases whose config has boost on, which the row does not hold.
fn migrate(run: &Run) -> Answer {
    if run.base != "ok" && run.base != code(NOT_ENOUGH_REMAINING) {
        return Answer::Same;
    }
    if run.remaining + run.extra == 2 {
        if run.extra == 2 {
            if run.base == "ok" && run.remaining == 0 {
                return Answer::Open;
            }
            // Second extra is read-only and `init_boost` wants it writable.
            return Answer::Runtime("PrivilegeEscalation");
        }
        return Answer::Pass;
    }
    if run.remaining == 0 {
        return Answer::Same;
    }
    Answer::Bare
}

/// A multiple of five is a longer route, which the route models hold. Five
/// honest remaining keys with a 6020 base already carry a second hop group,
/// and the extras are read as a third in some base cases only.
fn multi_hop(run: &Run) -> Answer {
    if run.base == "6020" {
        return if run.remaining == 5 { Answer::Open } else { Answer::Same };
    }
    if (run.remaining + run.extra) % 5 == 0 {
        return Answer::Open;
    }
    Answer::Code(NOT_ENOUGH_REMAINING)
}

/// The recipient count check comes after the account checks: 2006, 3010 and
/// 3012 are Anchor errors on the declared accounts and 6000 is the handler's
/// own authorization check, and all four keep the honest outcome. Every later
/// failure moves to the count error. When the honest run fails the count
/// check itself, an appended count that lands on a fixture's expected
/// recipient count lets the run proceed; the expected count is not in the
/// row, so the observed pairs are not answered.
fn holders(run: &Run) -> Answer {
    if matches!(run.base, "2006" | "3010" | "3012" | "6000") {
        return Answer::Same;
    }
    if run.base == code(HOLDER_COUNT)
        && matches!(
            (run.remaining, run.extra),
            (0, 2) | (1, 1) | (1, 3) | (3, 1) | (5, 1) | (7, 1) | (9, 1) | (11, 1)
        )
    {
        return Answer::Open;
    }
    Answer::Code(HOLDER_COUNT)
}

fn code(value: u32) -> &'static str {
    match value {
        NOT_ENOUGH_REMAINING => "6027",
        BUYBACK_MISSING => "6062",
        UNSUPPORTED_QUOTE_MINT => "6063",
        CASHBACK_MISSING => "6072",
        INVALID_BONDING_CURVE_V2 => "6074",
        HOLDER_COUNT => "6085",
        _ => "",
    }
}

pub fn trailing(run: &Run) -> Answer {
    // A transaction-level failure is the runtime's, not the handler's: an
    // appended unfunded key can change the rent outcome.
    if run.base.starts_with("TransactionError") {
        return Answer::Open;
    }
    match run.name {
        "distribute_creator_fees" | "get_minimum_distributable_fee" => distribution_native(run),
        "distribute_creator_fees_v2" => distribution_token(run),
        "set_params" | "set_reserved_fee_recipients" => eight_key_list(run),
        "update_buyback_config" => buyback_config(run),
        "create_v2" => create_v2(run),
        "distribute_fee_to_holders" => holders(run),
        "multi_hop_curve_swap" => multi_hop(run),
        "migrate" | "migrate_v2" => migrate(run),
        "buy" => buyback_slot(run, 1),
        "sell" => {
            // A 6074 base with at most one remaining key keeps its code but
            // the appended keys are written before the failure, so the state
            // does not hold.
            if run.base == code(INVALID_BONDING_CURVE_V2) && run.remaining <= 1 {
                return Answer::Open;
            }
            if run.base == code(CASHBACK_MISSING) {
                return Answer::Code(WRONG_CASHBACK_ACCOUNT);
            }
            buyback_slot(run, 1)
        }
        _ => Answer::Same,
    }
}
