//! Captured reading of accounts past the declared list of Pump commands.
//!
//! Anchor hands everything after the declared accounts to the handler as
//! `remaining_accounts` and checks none of it. Most commands never look, so any
//! number of extra keys changes nothing. A few read a fixed slot or test a count,
//! and for those the extras either fill a slot the honest list left empty or
//! break a count that used to hold.
//!
//! This model answers how an extra key changes a run that the existing models
//! already cover. `Same` means the run keeps its error, logs and account state,
//! so the handlers stay with their own models. Every extra is an unknown key that
//! no fixture holds; a slot-filling key that is valid would simply pass, and that
//! case is held by each command's own test.
//!
//! Commands with no arm below answer `Same`. That is confirmed only for the
//! commands the test reaches; for the others it is unconfirmed.
//!
//! Unconfirmed by the test, which stops each base test after 30 transactions and
//! does not reach these runs: the `buy` and `sell` slot arms (6062 to 6057, 6072 to
//! 6073), the token route of `distribute_creator_fees_v2`, and the
//! `get_minimum_distributable_fee` and `set_reserved_fee_recipients` arms. They
//! follow what a longer exploratory run on the captured program showed, but no
//! recorded comparison holds them.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_trailing_accounts_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.

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
/// `InvalidQuoteTokenProgram`.
pub const INVALID_QUOTE_PROGRAM: u32 = 6064;
/// `MissingCashbackAccounts`.
pub const CASHBACK_MISSING: u32 = 6072;
/// `InvalidCashbackAccumulator`.
pub const WRONG_CASHBACK_ACCOUNT: u32 = 6073;
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

/// Each row reads its recipient, then its ATA at `rows + i`.
fn distribution_token(run: &Run) -> Answer {
    if run.base != code(NOT_ENOUGH_REMAINING) {
        return Answer::Same;
    }
    let total = run.remaining + run.extra;
    for i in 0..run.rows {
        if i >= total || run.rows + i >= total {
            return Answer::Same;
        }
        if i >= run.remaining || run.rows + i >= run.remaining {
            return Answer::Code(WRONG_SHAREHOLDER);
        }
    }
    Answer::Same
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
/// reaches the quote check moves. Runs that fail later in the handler with no
/// remaining accounts are unconfirmed: no base case stops there.
fn create_v2(run: &Run) -> Answer {
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
        return Answer::Code(NOT_BUYBACK_RECIPIENT);
    }
    Answer::Same
}

/// The handler pattern-matches exactly two keys. Any other count takes the
/// no-boost branch, which is 6027 while the AMM config has boost on and a plain
/// skip otherwise, as the same call with no remaining accounts shows.
fn migrate(run: &Run) -> Answer {
    if run.base != "ok" && run.base != code(NOT_ENOUGH_REMAINING) {
        return Answer::Same;
    }
    if run.remaining + run.extra == 2 {
        // Second extra is read-only and `init_boost` wants it writable.
        return if run.extra == 2 { Answer::Runtime("PrivilegeEscalation") } else { Answer::Pass };
    }
    if run.remaining == 0 {
        return Answer::Same;
    }
    Answer::Bare
}

/// A multiple of five is a longer route, which the route models hold.
fn multi_hop(run: &Run) -> Answer {
    if run.base == "6020" {
        return Answer::Same;
    }
    if (run.remaining + run.extra) % 5 == 0 {
        return Answer::Open;
    }
    Answer::Code(NOT_ENOUGH_REMAINING)
}

fn code(value: u32) -> &'static str {
    match value {
        NOT_ENOUGH_REMAINING => "6027",
        BUYBACK_MISSING => "6062",
        CASHBACK_MISSING => "6072",
        _ => "",
    }
}

pub fn trailing(run: &Run) -> Answer {
    match run.name {
        "distribute_creator_fees" | "get_minimum_distributable_fee" => distribution_native(run),
        "distribute_creator_fees_v2" => distribution_token(run),
        "set_params" | "set_reserved_fee_recipients" => eight_key_list(run),
        "update_buyback_config" => buyback_config(run),
        "create_v2" => create_v2(run),
        "distribute_fee_to_holders" => Answer::Code(HOLDER_COUNT),
        "multi_hop_curve_swap" => multi_hop(run),
        "migrate" | "migrate_v2" => migrate(run),
        "buy" => buyback_slot(run, 1),
        "sell" => {
            if run.base == code(CASHBACK_MISSING) {
                return Answer::Code(WRONG_CASHBACK_ACCOUNT);
            }
            buyback_slot(run, 1)
        }
        _ => Answer::Same,
    }
}
