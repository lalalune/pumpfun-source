//! Captured account admission of Pump `set_params` and
//! `set_reserved_fee_recipients`: which accounts they refuse, with which code, and
//! which refusal wins when several are wrong, the remaining accounts included.
//!
//! `fee_params.rs` states the handlers' order and checks admission as two bits, the
//! signer and the stored authority. This model states the checks around them.
//! Recovered from `evidence/original/pump/deployed.so` and checked against it on
//! LiteSVM by `tests/test_fee_setter_admission_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.
//!
//! The arguments decode first. `global` then loads, `authority` is checked as a
//! signer, and a missing `event_authority` or `program` key ends the load. The
//! constraints follow: `global` seeds, its `mut`, the stored authority, `authority`
//! `mut` on `set_params` only, and `event_authority` seeds. The handler then reads
//! the remaining accounts. Nothing checks `program`: the call reaches it last, as a
//! missing account of the event CPI, after every write.
//!
//! Unconfirmed (미확인, outside the checked inputs): `global` lengths other than 4,
//! 8 and 1088.

pub const INSTRUCTION_DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const NOT_ENOUGH_ACCOUNT_KEYS: u32 = 3005;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const NOT_SIGNER: u32 = 3010;
pub const NOT_INITIALIZED: u32 = 3012;
pub const NOT_AUTHORIZED: u32 = 6000;

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
    /// The arguments end early. A setter without arguments cannot have this.
    pub short_arguments: bool,
    pub global: Load,
    pub global_wrong_address: bool,
    pub global_read_only: bool,
    /// `global.authority` is not the key in the `authority` slot.
    pub stored_authority_differs: bool,
    pub authority_unsigned: bool,
    pub authority_read_only: bool,
    /// `set_reserved_fee_recipients` takes a read-only `authority`.
    pub authority_needs_mut: bool,
    pub event_authority_wrong: bool,
    /// `event_authority` or `program` is left out of the instruction.
    pub account_dropped: bool,
}

fn load(r: &Request) -> Result<(), u32> {
    match r.global {
        Load::Missing => Err(NOT_INITIALIZED),
        Load::WrongOwner => Err(OWNED_BY_WRONG_PROGRAM),
        Load::Short => Err(DISCRIMINATOR_NOT_FOUND),
        Load::BadDiscriminator => Err(DISCRIMINATOR_MISMATCH),
        Load::Truncated => Err(DID_NOT_DESERIALIZE),
        Load::Stored => Ok(()),
    }
}

pub fn admit(r: &Request) -> Result<(), u32> {
    if r.short_arguments {
        return Err(INSTRUCTION_DID_NOT_DESERIALIZE);
    }
    load(r)?;
    if r.authority_unsigned {
        return Err(NOT_SIGNER);
    }
    if r.account_dropped {
        return Err(NOT_ENOUGH_ACCOUNT_KEYS);
    }
    if r.global_wrong_address {
        return Err(CONSTRAINT_SEEDS);
    }
    if r.global_read_only {
        return Err(CONSTRAINT_MUT);
    }
    if r.stored_authority_differs {
        return Err(NOT_AUTHORIZED);
    }
    if r.authority_needs_mut && r.authority_read_only {
        return Err(CONSTRAINT_MUT);
    }
    if r.event_authority_wrong {
        return Err(CONSTRAINT_SEEDS);
    }
    Ok(())
}
