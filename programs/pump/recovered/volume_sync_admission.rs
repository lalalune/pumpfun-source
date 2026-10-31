//! Captured account admission of Pump `sync_user_volume_accumulator`: which
//! accounts it refuses, with which code, and which refusal wins when several are
//! wrong.
//!
//! `token_incentives.rs` models the reset and takes well-formed accounts. This
//! model stops where that one starts. Recovered from
//! `evidence/original/pump/deployed.so` and checked against it on LiteSVM by
//! `tests/test_volume_sync_admission_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Both accumulators load first, in field order. The constraints then run in
//! field order. `user` is not a signer and is only a seed. `program` is not
//! checked: a wrong one only fails the event self-CPI, so a call that changes
//! nothing succeeds with it.
//!
//! Unconfirmed (미확인, outside the checked inputs): accumulators between 8 bytes
//! and their full length.

pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const NOT_INITIALIZED: u32 = 3012;

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum Load {
    #[default]
    Stored,
    Missing,
    WrongOwner,
    /// Four bytes.
    Short,
    BadDiscriminator,
    /// The discriminator and nothing else.
    Truncated,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct Request {
    pub user_wrong_address: bool,
    pub global: Load,
    pub global_wrong_address: bool,
    pub user_accumulator: Load,
    pub user_accumulator_wrong_address: bool,
    pub user_accumulator_read_only: bool,
    pub event_authority_wrong: bool,
}

fn load(slot: Load) -> Result<(), u32> {
    match slot {
        Load::Stored => Ok(()),
        Load::Missing => Err(NOT_INITIALIZED),
        Load::WrongOwner => Err(OWNED_BY_WRONG_PROGRAM),
        Load::Short => Err(DISCRIMINATOR_NOT_FOUND),
        Load::BadDiscriminator => Err(DISCRIMINATOR_MISMATCH),
        Load::Truncated => Err(DID_NOT_DESERIALIZE),
    }
}

pub fn admit(r: &Request) -> Result<(), u32> {
    load(r.global)?;
    load(r.user_accumulator)?;
    if r.global_wrong_address {
        return Err(CONSTRAINT_SEEDS);
    }
    // The accumulator's seeds name the user passed.
    if r.user_accumulator_wrong_address || r.user_wrong_address {
        return Err(CONSTRAINT_SEEDS);
    }
    if r.user_accumulator_read_only {
        return Err(CONSTRAINT_MUT);
    }
    if r.event_authority_wrong {
        return Err(CONSTRAINT_SEEDS);
    }
    Ok(())
}
