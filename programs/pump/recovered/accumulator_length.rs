//! Captured reading of the stored length of Pump's volume accumulators.
//!
//! `user_volume_accumulator` is created with 137 bytes, of which the decoder
//! uses 106. `global_volume_accumulator` is 544 bytes and uses all of them.
//! Every instruction that loads one applies the same two gates, ahead of its
//! handler; what differs is who loads it, and who also asks for exactly 137
//! bytes. The amounts and handler errors stay with each instruction's own
//! model, so `twin` below is the outcome of the same call on the standard
//! length.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_accumulator_length_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.

/// System `AccountAlreadyInUse`: an empty account reads as not created yet, and
/// the `allocate` of the creation path refuses a program-owned one.
pub const ACCOUNT_ALREADY_IN_USE: u32 = 0;
/// Anchor `ConstraintSpace`.
pub const CONSTRAINT_SPACE: u32 = 2019;
/// Anchor `AccountDiscriminatorNotFound`.
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
/// Anchor `AccountDidNotDeserialize`.
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const ACCOUNT_TYPE_NOT_SUPPORTED: u32 = 6010;
pub const INVALID_CASHBACK_ACCUMULATOR: u32 = 6073;

/// `space` of every `init_if_needed` on the user accumulator.
pub const USER_SPACE: u64 = 137;
/// Bytes the user accumulator decoder consumes: the fields end here, and bytes
/// past this offset are never read or written.
pub const USER_DECODED: u64 = 106;
pub const GLOBAL_DECODED: u64 = 544;

const LAMPORTS_PER_BYTE: u64 = 6_960;
const ACCOUNT_OVERHEAD: u64 = 128;

/// `Rent::minimum_balance(len)` under default rent.
pub fn rent(len: u64) -> u64 {
    (ACCOUNT_OVERHEAD + len) * LAMPORTS_PER_BYTE
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum UserRead {
    /// The account is not in the instruction, or the route never opens it.
    Ignored,
    /// `Account<UserVolumeAccumulator>`: `close`, `sync`, `claim_token_incentives`
    /// and the token route of `claim_cashback_v2`.
    Load,
    /// `init_if_needed, space = 137`: `buy`, `buy_exact_sol_in`, the v2 and v3
    /// trades, and `init_user_volume_accumulator`.
    InitIfNeeded,
    /// `Load`, and the claim pays out what stands above the rent of the real
    /// length: `claim_cashback` and the native route of `claim_cashback_v2`.
    NativeClaim,
    /// `sell` on a cashback coin with a creator fee to credit: the program
    /// checks the slot itself, pays, and only then decodes.
    CashbackSell,
    /// `extend_account`, which takes any account with a known discriminator.
    Extend,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Answer {
    /// The outcome of the standard length holds.
    Same,
    Error(u32),
    /// Succeeds, and this many lamports leave the accumulator.
    Paid(u64),
}

/// Anchor's `try_deserialize` on a program-owned account.
pub fn load(len: u64, decoded: u64) -> Option<u32> {
    if len < 8 {
        Some(DISCRIMINATOR_NOT_FOUND)
    } else if len < decoded {
        Some(DID_NOT_DESERIALIZE)
    } else {
        None
    }
}

/// The errors `sell` can raise after the cashback step, or inside it past the
/// decode: all of them lose to a failing decode. Anything else (slippage,
/// reserves) came before the step and stands.
fn after_cashback_step(error: u32) -> bool {
    matches!(error, 6024 | 6057 | 6062 | 6074)
}

pub fn user_accumulator(read: UserRead, len: u64, lamports: u64, twin: Option<u32>) -> Answer {
    match read {
        UserRead::Ignored => Answer::Same,
        UserRead::Load => match load(len, USER_DECODED) {
            Some(code) => Answer::Error(code),
            None => Answer::Same,
        },
        UserRead::InitIfNeeded => match load(len, USER_DECODED) {
            Some(code) => Answer::Error(code),
            None if len != USER_SPACE => Answer::Error(CONSTRAINT_SPACE),
            None => Answer::Same,
        },
        UserRead::NativeClaim => match load(len, USER_DECODED) {
            Some(code) => Answer::Error(code),
            None if twin.is_some() => Answer::Same,
            None => Answer::Paid(lamports.saturating_sub(rent(len))),
        },
        UserRead::CashbackSell => {
            if twin.map_or(false, |error| !after_cashback_step(error)) {
                return Answer::Same;
            }
            if len == 0 {
                return Answer::Error(ACCOUNT_ALREADY_IN_USE);
            }
            if len < 8 {
                return Answer::Error(INVALID_CASHBACK_ACCUMULATOR);
            }
            match load(len, USER_DECODED) {
                Some(code) => Answer::Error(code),
                None => Answer::Same,
            }
        }
        UserRead::Extend => {
            if len < 8 {
                Answer::Error(ACCOUNT_TYPE_NOT_SUPPORTED)
            } else {
                Answer::Same
            }
        }
    }
}

/// `reads` is false where the instruction does not take the account (`sell`,
/// `sell_v2`, v3 trades) or never decodes it (the claims of cashback).
pub fn global_accumulator(reads: bool, len: u64) -> Answer {
    match load(len, GLOBAL_DECODED) {
        Some(code) if reads => Answer::Error(code),
        _ => Answer::Same,
    }
}
