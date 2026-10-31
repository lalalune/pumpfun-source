//! Captured account admission of eleven Pump setters of `Global`: which accounts
//! they refuse, with which code, and which refusal wins when several are wrong.
//!
//! `global_admin.rs` and `global_lifecycle.rs` hold the bodies of these setters and
//! check admission as a list of bits on a few of them. This model states one order
//! and shows that all eleven share it. Recovered from
//! `evidence/original/pump/deployed.so` and checked against it on LiteSVM by
//! `tests/test_admin_setter_admission_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! The arguments decode first. `global` then loads, `authority` is checked as a
//! signer, and a missing `event_authority` or `program` key ends the load. The
//! constraints follow: `global` seeds, its `mut`, the stored authority, `authority`
//! `mut` where the setter asks for it, and `event_authority` seeds. Nothing checks
//! `program`: only a setter that emits an event reaches it, as a missing account of
//! the event CPI.
//!
//! Unconfirmed (미확인, outside the checked inputs): `set_params`,
//! `set_reserved_fee_recipients`, and `global` lengths other than 4, 8 and 1088.

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
    /// `update_global_authority` takes a read-only `authority`.
    pub authority_needs_mut: bool,
    pub event_authority_wrong: bool,
    /// `event_authority` or `program` is left out of the instruction.
    pub account_dropped: bool,
    pub program_wrong: bool,
    /// The setter emits through the event CPI, which names `program`.
    pub emits_event: bool,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    Code(u32),
    /// The event CPI names a program the instruction did not pass.
    MissingAccount,
}

fn code(c: u32) -> Stop {
    Stop::Code(c)
}

fn load(r: &Request) -> Result<(), Stop> {
    match r.global {
        Load::Missing => Err(code(NOT_INITIALIZED)),
        Load::WrongOwner => Err(code(OWNED_BY_WRONG_PROGRAM)),
        Load::Short => Err(code(DISCRIMINATOR_NOT_FOUND)),
        Load::BadDiscriminator => Err(code(DISCRIMINATOR_MISMATCH)),
        Load::Truncated => Err(code(DID_NOT_DESERIALIZE)),
        Load::Stored => Ok(()),
    }
}

pub fn admit(r: &Request) -> Result<(), Stop> {
    if r.short_arguments {
        return Err(code(INSTRUCTION_DID_NOT_DESERIALIZE));
    }
    load(r)?;
    if r.authority_unsigned {
        return Err(code(NOT_SIGNER));
    }
    if r.account_dropped {
        return Err(code(NOT_ENOUGH_ACCOUNT_KEYS));
    }
    if r.global_wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.global_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.stored_authority_differs {
        return Err(code(NOT_AUTHORIZED));
    }
    if r.authority_needs_mut && r.authority_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.event_authority_wrong {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.emits_event && r.program_wrong {
        return Err(Stop::MissingAccount);
    }
    Ok(())
}
