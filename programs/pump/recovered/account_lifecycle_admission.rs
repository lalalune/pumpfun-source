//! Captured account admission of Pump `init_user_volume_accumulator`,
//! `close_user_volume_accumulator` and `extend_account`: which accounts each one
//! refuses, with which code, and which refusal wins when several are wrong.
//!
//! `account_lifecycle.rs` decides on the state of the one account an instruction
//! points at, with every other account as expected. This model adds the other
//! accounts and the order. Recovered from `evidence/original/pump/deployed.so` and
//! checked against it on LiteSVM by
//! `tests/test_account_lifecycle_admission_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.
//!
//! `init_user_volume_accumulator` is `init_if_needed`: the accumulator's seeds come
//! before it is read, ahead of the `payer` and `mut` constraints. Which refusal a
//! wrong `payer` or a read-only account gives depends on whether the accumulator
//! exists: a CPI refuses it when it must be created, a constraint when it exists.
//! `close_user_volume_accumulator` loads first and checks `user`'s `mut` before the
//! accumulator's seeds. `extend_account` checks `mut` before `owner`.
//!
//! Unconfirmed (미확인, outside the checked inputs): accounts between 8 bytes and
//! their full length with other faults, and targets other than a short curve.

pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_OWNER: u32 = 2004;
pub const CONSTRAINT_RENT_EXEMPT: u32 = 2005;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const CONSTRAINT_SPACE: u32 = 2019;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const NOT_SIGNER: u32 = 3010;
pub const NOT_INITIALIZED: u32 = 3012;
/// System program `AccountAlreadyInUse`.
pub const ALREADY_IN_USE: u32 = 0;

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

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    Code(u32),
    PrivilegeEscalation,
}

fn code(c: u32) -> Stop {
    Stop::Code(c)
}

fn load_typed(load: Load) -> Result<(), Stop> {
    match load {
        Load::Stored => Ok(()),
        Load::Missing => Err(code(NOT_INITIALIZED)),
        Load::WrongOwner => Err(code(OWNED_BY_WRONG_PROGRAM)),
        Load::Short => Err(code(DISCRIMINATOR_NOT_FOUND)),
        Load::BadDiscriminator => Err(code(DISCRIMINATOR_MISMATCH)),
        Load::Truncated => Err(code(DID_NOT_DESERIALIZE)),
    }
}

/// The accumulator a create finds at its address.
#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum Fresh {
    #[default]
    Absent,
    /// System-owned and rent-exempt, so `payer` pays nothing.
    Funded,
    SystemData,
    ForeignOwner,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct InitRequest {
    pub payer_unsigned: bool,
    pub payer_read_only: bool,
    /// The `user` or accumulator key does not fit the accumulator's seeds.
    pub seeds_wrong: bool,
    pub accumulator_read_only: bool,
    pub system_program_wrong: bool,
    pub event_authority_wrong: bool,
}

fn init_prefix(r: &InitRequest) -> Result<(), Stop> {
    if r.payer_unsigned {
        return Err(code(NOT_SIGNER));
    }
    if r.system_program_wrong {
        return Err(code(INVALID_PROGRAM_ID));
    }
    if r.seeds_wrong {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}

/// `init_user_volume_accumulator` on an address with no accumulator. The system
/// CPI's own lamport check is `account_lifecycle::init`.
pub fn admit_create(r: &InitRequest, fresh: Fresh) -> Result<(), Stop> {
    init_prefix(r)?;
    if fresh == Fresh::ForeignOwner {
        return Err(code(OWNED_BY_WRONG_PROGRAM));
    }
    if r.accumulator_read_only {
        return Err(Stop::PrivilegeEscalation);
    }
    if fresh == Fresh::SystemData {
        return Err(code(ALREADY_IN_USE));
    }
    if r.payer_read_only && fresh == Fresh::Absent {
        return Err(Stop::PrivilegeEscalation);
    }
    Ok(())
}

/// What runs after the system CPI: a funded address gets past a read-only `payer`,
/// which then fails its own constraint, and the event authority's seeds.
pub fn after_create(r: &InitRequest) -> Result<(), Stop> {
    if r.payer_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.event_authority_wrong {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}

/// `init_user_volume_accumulator` on an existing accumulator.
pub fn admit_existing(r: &InitRequest, load: Load, oversized: bool, below_rent: bool) -> Result<(), Stop> {
    init_prefix(r)?;
    load_typed(load)?;
    if oversized {
        return Err(code(CONSTRAINT_SPACE));
    }
    if below_rent {
        return Err(code(CONSTRAINT_RENT_EXEMPT));
    }
    if r.accumulator_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    after_create(r)
}

#[derive(Clone, Copy, Default, Debug)]
pub struct CloseRequest {
    pub user_unsigned: bool,
    pub user_read_only: bool,
    pub accumulator: Load,
    pub accumulator_wrong_address: bool,
    pub accumulator_read_only: bool,
    pub event_authority_wrong: bool,
}

pub fn admit_close(r: &CloseRequest) -> Result<(), Stop> {
    if r.user_unsigned {
        return Err(code(NOT_SIGNER));
    }
    load_typed(r.accumulator)?;
    if r.user_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.accumulator_wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.accumulator_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.event_authority_wrong {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}

#[derive(Clone, Copy, Default, Debug)]
pub struct ExtendRequest {
    pub user_unsigned: bool,
    pub user_read_only: bool,
    pub system_program_wrong: bool,
    pub account_read_only: bool,
    /// Missing, or owned by another program.
    pub account_not_owned: bool,
    pub event_authority_wrong: bool,
}

/// The rest of `extend_account` is `account_lifecycle::extend`.
pub fn admit_extend(r: &ExtendRequest) -> Result<(), Stop> {
    if r.user_unsigned {
        return Err(code(NOT_SIGNER));
    }
    if r.system_program_wrong {
        return Err(code(INVALID_PROGRAM_ID));
    }
    if r.account_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.account_not_owned {
        return Err(code(CONSTRAINT_OWNER));
    }
    if r.user_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.event_authority_wrong {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}
