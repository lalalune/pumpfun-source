//! Captured Pump error log lines for the instructions the curve sweep and
//! global lifecycle tests drive: which source site or account each handler names when it fails, and the text
//! of the line Anchor logs for it.
//!
//! Checked against `evidence/original/pump/deployed.so` on LiteSVM by
//! `tests/test_error_sites_rest_captured.py`, which records the failing
//! transactions of those captured tests. Each row was read from a log of the
//! captured program. This is not a byte-identity claim.
//!
//! Unconfirmed: sites and accounts those tests do not reach, and the `Left:` /
//! `Right:` lines logged after some constraints.

/// How the line names the place that failed.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    /// `AnchorError thrown in programs/pump/src/<file>:<line>.`
    Thrown,
    /// `AnchorError caused by account: <name>.`
    Account,
    /// `ProgramError caused by account: <name>.`
    Program,
    /// `AnchorError occurred.`
    Occurred,
}

/// Code, variant name, message.
pub const ERRORS: &[(u64, &str, &str)] = &[
    (102, "InstructionDidNotDeserialize", "The program could not deserialize the given instruction."),
    (2000, "ConstraintMut", "A mut constraint was violated."),
    (2006, "ConstraintSeeds", "A seeds constraint was violated."),
    (3005, "AccountNotEnoughKeys", "Not enough account keys given to the instruction."),
    (3008, "InvalidProgramId", "Program ID was not as expected."),
    (3010, "AccountNotSigner", "The given account did not sign."),
    (3012, "AccountNotInitialized", "The program expected this account to be already initialized."),
    (6000, "NotAuthorized", "The given account is not authorized to execute this instruction.."),
    (6004, "MintDoesNotMatchBondingCurve", "The mint does not match the bonding curve.."),
    (6024, "Overflow", "Overflow."),
];

/// Handler, line form, place, code.
pub const SITES: &[(&str, Kind, &str, u64)] = &[
    ("initialize", Kind::Account, "global", 2006),
    ("initialize", Kind::Account, "system_program", 3005),
    ("initialize", Kind::Account, "system_program", 3008),
    ("initialize", Kind::Account, "user", 3005),
    ("initialize", Kind::Account, "user", 3010),
    ("sweep_creator_fee", Kind::Account, "bonding_curve", 6004),
    ("sweep_creator_fee", Kind::Thrown, "buy_v2.rs:60", 3012),
    ("sweep_creator_fee", Kind::Thrown, "sweep_fees.rs:123", 6000),
    ("sweep_creator_fee", Kind::Thrown, "sweep_fees.rs:145", 2006),
    ("sweep_protocol_fee", Kind::Account, "bonding_curve", 6004),
    ("sweep_protocol_fee", Kind::Thrown, "buy_v2.rs:60", 3012),
    ("sweep_protocol_fee", Kind::Thrown, "extend_account.rs:141", 6024),
    ("sweep_protocol_fee", Kind::Thrown, "fee_recipient.rs:19", 6000),
    ("sweep_protocol_fee", Kind::Thrown, "fee_recipient.rs:35", 6000),
    ("sweep_protocol_fee", Kind::Thrown, "lib.rs:2562", 6024),
    ("sweep_protocol_fee", Kind::Thrown, "sweep_fees.rs:123", 6000),
    ("toggle_cashback_enabled", Kind::Occurred, "", 102),
    ("toggle_cashback_enabled", Kind::Thrown, "lib.rs:121", 6000),
    ("toggle_create_v2", Kind::Account, "authority", 2000),
    ("toggle_create_v2", Kind::Account, "event_authority", 2006),
    ("toggle_create_v2", Kind::Account, "event_authority", 3005),
    ("toggle_create_v2", Kind::Account, "global", 6000),
    ("toggle_create_v2", Kind::Occurred, "", 102),
    ("toggle_create_v2", Kind::Thrown, "lib.rs:114", 6000),
    ("toggle_mayhem_mode", Kind::Occurred, "", 102),
    ("toggle_mayhem_mode", Kind::Thrown, "lib.rs:149", 6000),
    ("update_global_authority", Kind::Account, "authority", 3010),
    ("update_global_authority", Kind::Account, "event_authority", 2006),
    ("update_global_authority", Kind::Account, "global", 2000),
    ("update_global_authority", Kind::Account, "global", 6000),
    ("update_global_authority", Kind::Account, "program", 3005),
];

/// The whole log line, or `None` for a site the table does not hold.
pub fn line(handler: &str, kind: Kind, place: &str, code: u64) -> Option<String> {
    SITES.iter().find(|s| **s == (handler, kind, place, code))?;
    let (_, name, message) = ERRORS.iter().find(|e| e.0 == code)?;
    let head = match kind {
        Kind::Thrown => format!("AnchorError thrown in programs/pump/src/{place}."),
        Kind::Account => format!("AnchorError caused by account: {place}."),
        Kind::Program => format!("ProgramError caused by account: {place}."),
        Kind::Occurred => "AnchorError occurred.".to_string(),
    };
    Some(format!("{head} Error Code: {name}. Error Number: {code}. Error Message: {message}"))
}
