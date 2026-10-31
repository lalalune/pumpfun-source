//! Captured account admission of Pump `distribute_creator_fees_v2` on a native
//! coin: which accounts it refuses, with which code, and which refusal wins when
//! several are wrong.
//!
//! `creator_fee_distribution.rs` covers `distribute_creator_fees`, and
//! `creator_fee_distribution_quote.rs` the route of a coin with a quote mint. This
//! model covers the route between them: the v2 account list on a curve that names
//! no quote mint, where the quote mint slot takes wrapped SOL and the shares are
//! paid in lamports. Recovered from `evidence/original/pump/deployed.so` and checked
//! against it on LiteSVM by `tests/test_distribution_v2_native_admission_captured.py`.
//! Not linked into the SBF crate. This is not a byte-identity claim.
//!
//! Admission runs in two stages. Fields load in field order. The constraints then
//! run in field order. The vault's token account has seeds and `mut` here too,
//! and nothing else reads it, so it may be absent or hold anything. The quote mint
//! is the last field with a constraint: wrapped SOL on a native curve, and the
//! curve's mint on any other. Unlike `distribute_creator_fees`, a call that pays
//! nothing still emits its event.
//!
//! Unconfirmed (미확인, outside the checked inputs): Token-2022 accounts, and
//! accounts between 4 bytes and their full length.

pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const NOT_SIGNER: u32 = 3010;
pub const NOT_INITIALIZED: u32 = 3012;
pub const MINT_DOES_NOT_MATCH_BONDING_CURVE: u32 = 6004;
pub const CREATOR_MISMATCH: u32 = 6053;

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
    pub mint: Load,
    pub mint_wrong_address: bool,
    pub curve: Load,
    pub curve_wrong_address: bool,
    /// `bonding_curve.creator` is not the key in the `sharing_config` slot.
    pub creator_mismatch: bool,
    pub config: Load,
    /// Named by the curve, but not the `sharing-config` PDA of the mint.
    pub config_wrong_address: bool,
    /// `sharing_config.mint` is not the mint.
    pub config_mint_mismatch: bool,
    pub vault: AddressSlot,
    pub system_program_wrong: bool,
    pub event_authority_wrong: bool,
    pub program_wrong: bool,
    pub vault_token: AddressSlot,
    pub quote_mint: Load,
    /// Another mint in the slot, with the token account left as it was.
    pub quote_mint_seed_mismatch: bool,
    /// Another mint in the slot, with the token account of that mint.
    pub quote_mint_not_curves: bool,
    pub token_program: TokenProgramSlot,
    pub associated_program_wrong: bool,
}

/// The vault as the system transfer finds it.
#[derive(Clone, Copy, Default, Debug)]
pub struct NativeVault {
    pub foreign_owner: bool,
    pub has_data: bool,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    Code(u32),
    InvalidAccountData,
    /// The vault holds data.
    InvalidArgument,
    /// The vault's owner is not the system program.
    ExternalLamportSpend,
}

fn code(c: u32) -> Stop {
    Stop::Code(c)
}

fn load_common(load: Load) -> Result<(), Stop> {
    match load {
        Load::Missing => Err(code(NOT_INITIALIZED)),
        Load::WrongOwner => Err(code(OWNED_BY_WRONG_PROGRAM)),
        _ => Ok(()),
    }
}

/// `Account<T>`: the Anchor loader.
fn load_typed(load: Load) -> Result<(), Stop> {
    load_common(load)?;
    match load {
        Load::Short => Err(code(DISCRIMINATOR_NOT_FOUND)),
        Load::BadDiscriminator => Err(code(DISCRIMINATOR_MISMATCH)),
        Load::Truncated => Err(code(DID_NOT_DESERIALIZE)),
        _ => Ok(()),
    }
}

/// `InterfaceAccount<T>`, and the bonding curve's length-keyed decoder.
fn load_decoded(load: Load) -> Result<(), Stop> {
    load_common(load)?;
    if load == Load::Stored {
        Ok(())
    } else {
        Err(Stop::InvalidAccountData)
    }
}

fn load_stage(r: &Request) -> Result<(), Stop> {
    if r.payer_unsigned {
        return Err(code(NOT_SIGNER));
    }
    load_decoded(r.mint)?;
    load_decoded(r.curve)?;
    load_typed(r.config)?;
    if r.system_program_wrong || r.program_wrong {
        return Err(code(INVALID_PROGRAM_ID));
    }
    load_decoded(r.quote_mint)?;
    if r.token_program == TokenProgramSlot::Invalid || r.associated_program_wrong {
        return Err(code(INVALID_PROGRAM_ID));
    }
    Ok(())
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
    if r.mint_wrong_address || r.curve_wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.creator_mismatch {
        return Err(code(CREATOR_MISMATCH));
    }
    if r.config_wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.config_mint_mismatch {
        return Err(code(MINT_DOES_NOT_MATCH_BONDING_CURVE));
    }
    seeded(&r.vault, false)?;
    if r.event_authority_wrong {
        return Err(code(CONSTRAINT_SEEDS));
    }
    let token_seed = r.quote_mint_seed_mismatch || r.token_program == TokenProgramSlot::OtherInterface;
    seeded(&r.vault_token, token_seed)?;
    if r.quote_mint_not_curves {
        return Err(code(MINT_DOES_NOT_MATCH_BONDING_CURVE));
    }
    Ok(())
}

pub fn admit(r: &Request) -> Result<(), Stop> {
    load_stage(r)?;
    constraint_stage(r)
}

/// The refusal of the first share's transfer. A call that pays nothing makes no
/// transfer, so none of these show.
pub fn vault_transfer(vault: &NativeVault) -> Result<(), Stop> {
    if vault.has_data {
        return Err(Stop::InvalidArgument);
    }
    if vault.foreign_owner {
        return Err(Stop::ExternalLamportSpend);
    }
    Ok(())
}
