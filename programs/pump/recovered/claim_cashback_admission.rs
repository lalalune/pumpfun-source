//! Captured account admission of Pump `claim_cashback`: which accounts it refuses,
//! with which code, and which refusal wins when several are wrong.
//!
//! `claim_cashback.rs` covers `user` and the accumulator, and takes the program
//! slots as given. This model adds `system_program`, `event_authority` and `program`
//! to the order. Recovered from `evidence/original/pump/deployed.so` and checked
//! against it on LiteSVM by `tests/test_claim_cashback_admission_captured.py`. Not
//! linked into the SBF crate. This is not a byte-identity claim.
//!
//! Admission runs in two stages. Accounts load in field order: the accumulator,
//! then the two programs. `user` is an unchecked account, so nothing about it is
//! read until the constraints, which run in field order, each seeded account as
//! seeds before `mut`. A wrong `event_authority` is refused on a call that pays
//! nothing and emits no event, too.
//!
//! Unconfirmed (미확인, outside the checked inputs): accumulators between 8 bytes
//! and their decoded length with other faults.

pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
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
    /// The discriminator and nothing else, or an invalid bool in the fields.
    Undecodable,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct Request {
    pub user_read_only: bool,
    /// The `user` or accumulator key does not fit the accumulator's seeds.
    pub seeds_wrong: bool,
    pub accumulator: Load,
    pub accumulator_read_only: bool,
    pub system_program_wrong: bool,
    pub program_wrong: bool,
    pub event_authority_wrong: bool,
}

pub fn admit(r: &Request) -> Result<(), u32> {
    match r.accumulator {
        Load::Stored => {}
        Load::Missing => return Err(NOT_INITIALIZED),
        Load::WrongOwner => return Err(OWNED_BY_WRONG_PROGRAM),
        Load::Short => return Err(DISCRIMINATOR_NOT_FOUND),
        Load::BadDiscriminator => return Err(DISCRIMINATOR_MISMATCH),
        Load::Undecodable => return Err(DID_NOT_DESERIALIZE),
    }
    if r.system_program_wrong || r.program_wrong {
        return Err(INVALID_PROGRAM_ID);
    }
    if r.user_read_only {
        return Err(CONSTRAINT_MUT);
    }
    if r.seeds_wrong {
        return Err(CONSTRAINT_SEEDS);
    }
    if r.accumulator_read_only {
        return Err(CONSTRAINT_MUT);
    }
    if r.event_authority_wrong {
        return Err(CONSTRAINT_SEEDS);
    }
    Ok(())
}
