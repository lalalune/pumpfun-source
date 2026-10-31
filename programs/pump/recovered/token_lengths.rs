//! Captured reading of the stored length of token accounts and mints.
//!
//! A Pump instruction reads a token account or mint in one of a few ways, and
//! each has its own idea of which lengths are fine. `read_of` names the way per
//! instruction and slot; `answer` says what a stored length does to a call that
//! otherwise has the outcome of the standard length (the twin). Amounts and
//! handler errors stay with each instruction's own model.
//!
//! The Pump decoder takes the exact base length, or at least 167 bytes with the
//! account type byte at offset 165 (166 is one byte short for it). The captured
//! SPL Token program takes only the exact base length, and the captured
//! Token-2022 program also takes 166 tagged bytes. A slot the program opens with
//! a longer account therefore passes Pump and fails at the first token CPI.
//!
//! Unconfirmed: whether a handler read comes before every handler error of the
//! instruction. Only the failing twins of the replayed cases were seen, and all
//! of them stood.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured token
//! programs by `tests/test_token_lengths_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.

pub const TOKEN_LEN: u64 = 165;
pub const MINT_LEN: u64 = 82;
/// Shortest tagged account the Pump decoder takes.
pub const PUMP_TAGGED: u64 = 167;
/// Shortest tagged account captured Token-2022 takes.
pub const T22_TAGGED: u64 = 166;
/// `GetAccountDataSize`, which ATA creation sends first.
pub const OP_GET_ACCOUNT_DATA_SIZE: u8 = 21;
pub const SHARING_RECIPIENT_EMPTY: u32 = 6070;
/// SPL Token `InvalidMint`.
pub const TOKEN_INVALID_MINT: u32 = 2;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Read {
    /// `InterfaceAccount`: fails ahead of the handler.
    Load,
    /// Opened by the handler, behind the errors of the failing twins.
    Handler,
    /// A shareholder ATA: empty means not created, anything else is left to the
    /// token program.
    Recipient,
    /// A holder ATA: the idempotent create refuses an empty token-owned account.
    HolderAta,
    /// Opened by the ATA program's idempotent create.
    IdempotentAta,
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
        ("buy", "associated_bonding_curve" | "associated_user" | "mint") => Read::Load,
        ("buy_exact_quote_in_v2", "associated_base_bonding_curve" | "associated_base_user" | "base_mint" | "quote_mint") => Read::Load,
        ("buy_exact_quote_in_v3", "associated_base_bonding_curve" | "associated_base_user" | "base_mint" | "quote_mint") => Read::Load,
        ("buy_exact_sol_in", "associated_bonding_curve" | "associated_user" | "mint") => Read::Load,
        ("buy_v2", "associated_base_bonding_curve" | "associated_base_user" | "base_mint" | "quote_mint") => Read::Load,
        ("buy_v3", "associated_base_bonding_curve" | "associated_base_user" | "base_mint" | "quote_mint") => Read::Load,
        ("claim_token_incentives", "global_incentive_token_account" | "mint" | "user_ata") => Read::Load,
        ("collect_creator_fee_v2", "quote_mint") => Read::Load,
        ("distribute_creator_fees_v2", "mint" | "quote_mint") => Read::Load,
        ("distribute_fee_to_holders", "holder_rewards_token_account" | "quote_mint") => Read::Load,
        ("migrate", "associated_bonding_curve" | "mint" | "wsol_mint") => Read::Load,
        ("migrate_v2", "associated_base_bonding_curve" | "base_mint" | "quote_mint") => Read::Load,
        ("multi_hop_curve_swap", "destination" | "source") => Read::Load,
        ("sell", "associated_bonding_curve" | "associated_user" | "mint") => Read::Load,
        ("sell_v2", "associated_base_bonding_curve" | "associated_base_user" | "base_mint" | "quote_mint") => Read::Load,
        ("sell_v3", "associated_base_bonding_curve" | "associated_base_user" | "base_mint" | "quote_mint") => Read::Load,
        ("sweep_creator_fee", "base_mint" | "quote_mint") => Read::Load,
        ("sweep_protocol_fee", "base_mint" | "quote_mint") => Read::Load,
        ("buy_exact_quote_in_v2", "associated_creator_vault" | "associated_quote_bonding_curve" | "associated_quote_buyback_fee_recipient" | "associated_quote_fee_recipient" | "associated_quote_user" | "associated_user_volume_accumulator") => Read::Handler,
        ("buy_exact_quote_in_v3", "associated_quote_bonding_curve" | "associated_quote_user" | "buyback_fee_recipient") => Read::Handler,
        ("buy_v2", "associated_creator_vault" | "associated_quote_bonding_curve" | "associated_quote_buyback_fee_recipient" | "associated_quote_fee_recipient" | "associated_quote_user" | "associated_user_volume_accumulator") => Read::Handler,
        ("buy_v3", "associated_quote_bonding_curve" | "associated_quote_user" | "buyback_fee_recipient") => Read::Handler,
        ("migrate_v2", "user_pool_token_account") => Read::Handler,
        ("multi_hop_curve_swap", "rem0" | "rem1" | "rem3") => Read::Handler,
        ("sell_v2", "associated_creator_vault" | "associated_quote_bonding_curve" | "associated_quote_buyback_fee_recipient" | "associated_quote_fee_recipient" | "associated_quote_user" | "associated_user_volume_accumulator") => Read::Handler,
        ("sell_v3", "associated_quote_bonding_curve" | "associated_quote_user" | "buyback_fee_recipient") => Read::Handler,
        ("distribute_creator_fees_v2", "rem3" | "rem4" | "rem5") => Read::Recipient,
        ("distribute_fee_to_holders", "rem1") => Read::HolderAta,
        ("migrate_v2", "pool_authority_quote_account") => Read::IdempotentAta,
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
        Read::Recipient if twin_ok && len == 0 => return Answer::PumpCode(SHARING_RECIPIENT_EMPTY),
        Read::HolderAta if twin_ok && len == 0 => return Answer::AtaIllegalOwner,
        Read::IdempotentAta if twin_ok && !parsed => return Answer::AtaIllegalOwner,
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
