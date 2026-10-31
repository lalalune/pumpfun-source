//! Captured account admission of Pump `sweep_protocol_fee` and
//! `sweep_creator_fee`: which accounts they refuse, with which code, which
//! refusal wins when several are wrong, and how far the token route reads the
//! token accounts Anchor leaves unchecked.
//!
//! `sweep_fees.rs` starts after the Anchor checks, apart from the mint and
//! recipient cases it names, and takes readable token accounts. This model adds
//! the rest. Recovered from `evidence/original/pump/deployed.so` and checked
//! against it on LiteSVM by `tests/test_sweep_account_admission_captured.py`.
//! Not linked into the SBF crate. This is not a byte-identity claim.
//!
//! Admission runs in two stages. Fields load in field order. The constraints
//! then run in field order, with the bonding curve's `quote_mint` constraint
//! after its seeds and `mut`, and `event_authority` last. `program` is not
//! checked: a wrong one only fails the event self-CPI, so a sweep of an empty
//! bucket succeeds with it.
//!
//! Unconfirmed (미확인, outside the checked inputs): Token-2022 accounts, and
//! accounts or mints between 4 bytes and their full length.

pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const NOT_SIGNER: u32 = 3010;
pub const NOT_INITIALIZED: u32 = 3012;
pub const MINT_DOES_NOT_MATCH_BONDING_CURVE: u32 = 6004;
pub const ACCOUNT_TYPE_NOT_SUPPORTED: u32 = 6010;
/// SPL Token codes, from the transfer.
pub const TOKEN_OWNER_MISMATCH: u32 = 4;
pub const TOKEN_FROZEN: u32 = 17;

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum Load {
    #[default]
    Stored,
    Missing,
    WrongOwner,
    /// Four bytes.
    Short,
    BadDiscriminator,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct AddressSlot {
    pub wrong_address: bool,
    pub read_only: bool,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum TokenProgramSlot {
    #[default]
    Expected,
    /// Token-2022, so the token account seeds no longer match.
    OtherInterface,
    Invalid,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct Request {
    pub payer_unsigned: bool,
    pub payer_read_only: bool,
    pub global: Load,
    pub global_wrong_address: bool,
    pub base_mint: Load,
    pub base_mint_wrong_address: bool,
    pub quote_mint: Load,
    pub quote_mint_wrong: bool,
    pub token_program: TokenProgramSlot,
    pub associated_program_wrong: bool,
    pub system_program_wrong: bool,
    pub curve: Load,
    pub curve_slot: AddressSlot,
    pub curve_token: AddressSlot,
    pub recipient_read_only: bool,
    pub recipient_token: AddressSlot,
    pub event_authority_wrong: bool,
}

/// A token account's bytes. The admission never reads them.
#[derive(Clone, Copy, Default, Debug)]
pub struct TokenState {
    pub missing: bool,
    pub foreign_owner: bool,
    /// Four bytes.
    pub short: bool,
    pub wrong_mint: bool,
    pub wrong_authority: bool,
    pub frozen: bool,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    Code(u32),
    InvalidAccountData,
}

fn code(c: u32) -> Stop {
    Stop::Code(c)
}

/// `Account<T>`: the Anchor loader.
fn load_typed(load: Load) -> Result<(), Stop> {
    match load {
        Load::Stored => Ok(()),
        Load::Missing => Err(code(NOT_INITIALIZED)),
        Load::WrongOwner => Err(code(OWNED_BY_WRONG_PROGRAM)),
        Load::Short => Err(code(DISCRIMINATOR_NOT_FOUND)),
        Load::BadDiscriminator => Err(code(DISCRIMINATOR_MISMATCH)),
    }
}

/// `InterfaceAccount<T>`, and the bonding curve's length-keyed decoder.
fn load_decoded(load: Load) -> Result<(), Stop> {
    match load {
        Load::Stored => Ok(()),
        Load::Missing => Err(code(NOT_INITIALIZED)),
        Load::WrongOwner => Err(code(OWNED_BY_WRONG_PROGRAM)),
        Load::Short | Load::BadDiscriminator => Err(Stop::InvalidAccountData),
    }
}

fn load_stage(r: &Request) -> Result<(), Stop> {
    if r.payer_unsigned {
        return Err(code(NOT_SIGNER));
    }
    load_typed(r.global)?;
    load_decoded(r.base_mint)?;
    load_decoded(r.quote_mint)?;
    if r.token_program == TokenProgramSlot::Invalid || r.associated_program_wrong || r.system_program_wrong {
        return Err(code(INVALID_PROGRAM_ID));
    }
    load_decoded(r.curve)
}

fn seeded(slot: &AddressSlot, wrong_seed: bool) -> Result<(), Stop> {
    if slot.wrong_address || wrong_seed {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if slot.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    Ok(())
}

fn constraint_stage(r: &Request) -> Result<(), Stop> {
    if r.payer_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.global_wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    seeded(&r.curve_slot, r.base_mint_wrong_address)?;
    if r.quote_mint_wrong {
        return Err(code(MINT_DOES_NOT_MATCH_BONDING_CURVE));
    }
    let token_seed = r.token_program == TokenProgramSlot::OtherInterface;
    seeded(&r.curve_token, token_seed)?;
    if r.recipient_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    seeded(&r.recipient_token, false)?;
    if r.event_authority_wrong {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}

pub fn admit(r: &Request) -> Result<(), Stop> {
    load_stage(r)?;
    constraint_stage(r)
}

/// The token bucket's checks, once there is an amount to move. The curve's
/// account is read first and the recipient's next. A missing recipient account
/// is created, so it has nothing to refuse. The recipient account's stored
/// authority is never read: only its address is bound to the recipient.
pub fn token_route(source: &TokenState, destination: &TokenState) -> Result<(), Stop> {
    if source.missing {
        return Err(code(NOT_INITIALIZED));
    }
    read_token(source)?;
    if !destination.missing {
        read_token(destination)?;
    }
    if source.frozen || (destination.frozen && !destination.missing) {
        return Err(code(TOKEN_FROZEN));
    }
    if source.wrong_authority {
        return Err(code(TOKEN_OWNER_MISMATCH));
    }
    Ok(())
}

fn read_token(token: &TokenState) -> Result<(), Stop> {
    if token.foreign_owner {
        return Err(code(ACCOUNT_TYPE_NOT_SUPPORTED));
    }
    if token.short {
        return Err(Stop::InvalidAccountData);
    }
    if token.wrong_mint {
        return Err(code(MINT_DOES_NOT_MATCH_BONDING_CURVE));
    }
    Ok(())
}
