//! Captured reading of the stored length of the three slots
//! `token_lengths.rs` leaves out, because a route decides how each is read.
//! Each slot below was measured on the route its own captured test takes,
//! and the three read three different ways.
//!
//! - `creator_vault_quote_token_account` on `distribute_creator_fees_v2`
//!   (the quote distribution route) is a `Load` read: a length the Pump
//!   decoder does not take fails `InvalidAccountData` ahead of the handler,
//!   even when the twin fails with a handler error (6024 in the recorded
//!   case), and a taken length is handed to the token program.
//! - `user_pool_token_account` on `migrate` is a `Handler` read, the same
//!   arm `token_lengths.rs` records for the `migrate_v2` slot of the same
//!   name: a passing call refuses an untaken length with
//!   `InvalidAccountData`, and the recorded failing twin (6000) keeps its
//!   error at every length.
//! - `buyback_fee_recipient` on `multi_hop_curve_swap` is decided by the
//!   route the case takes. On the recorded passing route nothing reads it:
//!   every length, 0 included, keeps the outcome, and no token instruction
//!   names it. On the recorded failing route (twin 6004) it is read ahead
//!   of the twin's error, like a `Load` read. Which routes reach the read
//!   is not in the row, so other routes of this instruction are
//!   unconfirmed; the arm below carries the two recorded routes only.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured
//! token programs by `tests/test_token_lengths_skipped_slots_captured.py`.
//! Not linked into the SBF crate. This is not a byte-identity claim.

pub const TOKEN_LEN: u64 = 165;
pub const MINT_LEN: u64 = 82;
/// Shortest tagged account the Pump decoder takes.
pub const PUMP_TAGGED: u64 = 167;
/// Shortest tagged account captured Token-2022 takes.
pub const T22_TAGGED: u64 = 166;
/// `GetAccountDataSize`, which ATA creation sends first.
pub const OP_GET_ACCOUNT_DATA_SIZE: u8 = 21;
/// SPL Token `InvalidMint`.
pub const TOKEN_INVALID_MINT: u32 = 2;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Read {
    /// `InterfaceAccount`: fails ahead of the handler.
    Load,
    /// Opened by the handler, behind the errors of the failing twins.
    Handler,
    /// Read on the recorded failing route ahead of its error, not read on
    /// the recorded passing route.
    BuybackRoute,
    Unread,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    Token,
    Mint,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Answer {
    Same,
    PumpInvalidData,
    PumpCode(u32),
    AtaIllegalOwner,
    TokenInvalidData,
    TokenCode(u32),
}

fn base(kind: Kind) -> u64 {
    match kind {
        Kind::Token => TOKEN_LEN,
        Kind::Mint => MINT_LEN,
    }
}

pub fn pump_parses(kind: Kind, len: u64, tagged: bool) -> bool {
    len == base(kind) || (len >= PUMP_TAGGED && tagged)
}

pub fn token_parses(t22: bool, kind: Kind, len: u64, tagged: bool) -> bool {
    len == base(kind) || (t22 && len >= T22_TAGGED && tagged)
}

pub fn read_of(instruction: &str, slot: &str) -> Read {
    match (instruction, slot) {
        ("distribute_creator_fees_v2", "creator_vault_quote_token_account") => Read::Load,
        ("migrate", "user_pool_token_account") => Read::Handler,
        ("multi_hop_curve_swap", "buyback_fee_recipient") => Read::BuybackRoute,
        _ => Read::Unread,
    }
}

/// `twin_ok` is whether the standard length succeeds, `first_op` the first
/// token instruction that names this account in the twin.
pub fn answer(read: Read, t22: bool, kind: Kind, len: u64, tagged: bool, twin_ok: bool, first_op: Option<u8>) -> Answer {
    let parsed = pump_parses(kind, len, tagged);
    match read {
        Read::Load if !parsed => return Answer::PumpInvalidData,
        Read::Handler if twin_ok && !parsed => return Answer::PumpInvalidData,
        Read::BuybackRoute if !twin_ok && !parsed => return Answer::PumpInvalidData,
        _ => {}
    }
    match first_op {
        Some(op) if !token_parses(t22, kind, len, tagged) => {
            if kind == Kind::Mint && op == OP_GET_ACCOUNT_DATA_SIZE {
                Answer::TokenCode(TOKEN_INVALID_MINT)
            } else {
                Answer::TokenInvalidData
            }
        }
        _ => Answer::Same,
    }
}
