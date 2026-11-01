//! Captured account admission of Pump legacy `create`: which accounts it refuses,
//! with which code, and which refusal wins when several are wrong.
//!
//! `legacy_create.rs` takes a set of faults and answers with the smallest one, for
//! six faults. This model states the whole order for all 14 accounts. Recovered
//! from `evidence/original/pump/deployed.so` and checked against it on LiteSVM by
//! `tests/test_create_admission_captured.py`. Not linked into the SBF crate. This
//! is not a byte-identity claim.
//!
//! Admission here is not two clean stages. The loads run first, with `global` ahead
//! of every other check. The three `init` accounts then run their system and
//! Associated Token CPIs in field order, each before any constraint of a later
//! field, so `mint_authority` is only compared after the mint and the curve exist.
//! `user` pays each of those CPIs, so a read-only or empty `user` stops at the first
//! one that needs lamports: an account funded beforehand takes none.
//!
//! Unconfirmed (미확인, outside the checked inputs): the bodies of a `metadata`
//! account, and accounts between 4 bytes and their full length.

pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const NOT_SIGNER: u32 = 3010;
pub const NOT_INITIALIZED: u32 = 3012;
pub const SYSVAR_MISMATCH: u32 = 3015;
/// System program `AccountAlreadyInUse`.
pub const ALREADY_IN_USE: u32 = 0;
/// System program `ResultWithNegativeLamports`.
pub const INSUFFICIENT_LAMPORTS: u32 = 1;

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

/// An `init` account.
#[derive(Clone, Copy, Default, Debug)]
pub struct NewAccount {
    pub read_only: bool,
    /// It already holds data under its program.
    pub taken: bool,
    /// System-owned and rent-exempt, so `user` pays nothing for it.
    pub funded: bool,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct Request {
    pub mint: NewAccount,
    pub mint_unsigned: bool,
    /// Another signing mint, so the curve's seeds no longer match.
    pub mint_other: bool,
    pub mint_authority_wrong: bool,
    pub curve: NewAccount,
    pub curve_wrong_address: bool,
    pub curve_token: NewAccount,
    pub curve_token_wrong_address: bool,
    pub global: Load,
    /// `global` decodes badly: an `initialized` byte of 2.
    pub global_invalid_bool: bool,
    pub global_wrong_address: bool,
    pub metadata_program_wrong: bool,
    pub metadata_wrong_address: bool,
    pub metadata_read_only: bool,
    pub user_unsigned: bool,
    pub user_read_only: bool,
    /// `user` holds too little to pay rent.
    pub user_poor: bool,
    pub system_program_wrong: bool,
    pub token_program_wrong: bool,
    pub associated_program_wrong: bool,
    pub rent_wrong: bool,
    pub event_authority_wrong: bool,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    Code(u32),
    PrivilegeEscalation,
    MissingAccount,
    IllegalOwner,
}

fn code(c: u32) -> Stop {
    Stop::Code(c)
}

fn load_stage(r: &Request) -> Result<(), Stop> {
    match r.global {
        Load::Missing => return Err(code(NOT_INITIALIZED)),
        Load::WrongOwner => return Err(code(OWNED_BY_WRONG_PROGRAM)),
        Load::Short => return Err(code(DISCRIMINATOR_NOT_FOUND)),
        Load::BadDiscriminator => return Err(code(DISCRIMINATOR_MISMATCH)),
        Load::Truncated => return Err(code(DID_NOT_DESERIALIZE)),
        Load::Stored => {}
    }
    if r.global_invalid_bool {
        return Err(code(DID_NOT_DESERIALIZE));
    }
    if r.metadata_program_wrong {
        return Err(code(INVALID_PROGRAM_ID));
    }
    if r.user_unsigned {
        return Err(code(NOT_SIGNER));
    }
    if r.system_program_wrong || r.token_program_wrong || r.associated_program_wrong {
        return Err(code(INVALID_PROGRAM_ID));
    }
    if r.rent_wrong {
        return Err(code(SYSVAR_MISMATCH));
    }
    Ok(())
}

fn pay(r: &Request, account: &NewAccount) -> Result<(), Stop> {
    if account.funded {
        return Ok(());
    }
    if r.user_read_only {
        return Err(Stop::PrivilegeEscalation);
    }
    if r.user_poor {
        return Err(code(INSUFFICIENT_LAMPORTS));
    }
    Ok(())
}

fn system_init(r: &Request, account: &NewAccount, unsigned: bool) -> Result<(), Stop> {
    if account.read_only || unsigned {
        return Err(Stop::PrivilegeEscalation);
    }
    if account.taken {
        return Err(code(ALREADY_IN_USE));
    }
    pay(r, account)
}

fn init_stage(r: &Request) -> Result<(), Stop> {
    system_init(r, &r.mint, r.mint_unsigned)?;
    if r.mint_other || r.curve_wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    system_init(r, &r.curve, false)?;
    if r.curve_token_wrong_address {
        return Err(Stop::MissingAccount);
    }
    // The CPI names `user` writable, whatever it ends up paying.
    if r.curve_token.read_only || r.user_read_only {
        return Err(Stop::PrivilegeEscalation);
    }
    if r.curve_token.taken {
        return Err(Stop::IllegalOwner);
    }
    pay(r, &r.curve_token)
}

fn constraint_stage(r: &Request) -> Result<(), Stop> {
    if r.mint_authority_wrong || r.global_wrong_address || r.metadata_wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.metadata_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.event_authority_wrong {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}

/// An empty `user` that funded nothing yet still has one CPI to pay: the metadata account.
pub fn last_payment(r: &Request) -> Result<(), Stop> {
    if r.user_poor {
        return Err(code(INSUFFICIENT_LAMPORTS));
    }
    Ok(())
}

pub fn admit(r: &Request) -> Result<(), Stop> {
    load_stage(r)?;
    init_stage(r)?;
    constraint_stage(r)
}
