//! Captured reading of the stored length of token accounts and mints on the
//! `create_v2` route, which `token_lengths.rs` does not cover.
//!
//! A created pool can name a quote mint in the remaining accounts. That mint
//! (slot `rem0`) is the one stored token account or mint the route reads: on a
//! call that otherwise succeeds, a mint the Pump decoder does not take (not
//! the exact 82 bytes, and not at least 167 bytes with the account type byte
//! at offset 165) is refused with the custom error 6063
//! (`UnsupportedQuoteMint`) ahead of the handler's other work, and a mint it
//! takes is handed to the token program, whose own reading is the one
//! `token_lengths.rs` describes. The pre-existing quote ATA (slot `rem1`)
//! shows no length reading at all in these rows: the only twins that carry
//! one fail at the ATA program's owner check, which is not a length read,
//! and every stored length keeps that outcome.
//!
//! Both failing twins stand ahead of the mint read as well: with too few
//! remaining accounts the call fails 6027, and with a pre-existing quote ATA
//! it fails at the ATA program, at every stored length of either slot. The
//! route's own mint is written by the run, not read: the fixture cases that
//! pre-store it fail on other programs' errors, never on a length.
//!
//! Unconfirmed: a passing twin whose quote mint is an SPL Token mint. Every
//! passing quote case in the fixture uses a Token-2022 quote mint, so the
//! token-program tail of the mint read (a Pump-parsed length the token
//! program does not take, reached through `GetAccountDataSize`) is carried
//! from the shared reading in `token_lengths.rs`, not from a row here. A
//! passing twin with a pre-existing quote ATA likewise does not occur: on a
//! passing call the ATA is created by the run.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured
//! token programs by `tests/test_token_lengths_create_v2_captured.py`. Not
//! linked into the SBF crate. This is not a byte-identity claim.

pub const TOKEN_LEN: u64 = 165;
pub const MINT_LEN: u64 = 82;
/// Shortest tagged account the Pump decoder takes.
pub const PUMP_TAGGED: u64 = 167;
/// Shortest tagged account captured Token-2022 takes.
pub const T22_TAGGED: u64 = 166;
/// `GetAccountDataSize`, which ATA creation sends first.
pub const OP_GET_ACCOUNT_DATA_SIZE: u8 = 21;
/// Pump custom error for a quote mint it does not take.
pub const UNSUPPORTED_QUOTE_MINT: u32 = 6063;
/// SPL Token `InvalidMint`.
pub const TOKEN_INVALID_MINT: u32 = 2;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Read {
    /// The quote mint in the remaining accounts: read on a passing call,
    /// behind the failing twins' earlier failures.
    QuoteMint,
    /// The pre-existing quote ATA: no length reading in these rows.
    QuoteAta,
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
        ("create_v2", "rem0") => Read::QuoteMint,
        ("create_v2", "rem1") => Read::QuoteAta,
        _ => Read::Unread,
    }
}

/// `twin_ok` is whether the standard length succeeds, `first_op` the first
/// token instruction that names this account in the twin.
pub fn answer(read: Read, t22: bool, kind: Kind, len: u64, tagged: bool, twin_ok: bool, first_op: Option<u8>) -> Answer {
    match read {
        Read::QuoteMint if twin_ok && !pump_parses(kind, len, tagged) => {
            return Answer::PumpCode(UNSUPPORTED_QUOTE_MINT);
        }
        // A failing twin fails ahead of both reads, at every length.
        Read::QuoteMint | Read::QuoteAta if !twin_ok => return Answer::Same,
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
