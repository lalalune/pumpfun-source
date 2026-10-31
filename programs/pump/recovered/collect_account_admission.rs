//! Captured account admission of Pump `collect_creator_fee` and
//! `collect_creator_fee_v2`: which accounts each one refuses, with which code,
//! and which refusal wins when several are wrong.
//!
//! `creator_fee_collect.rs` starts after admission and takes well-formed
//! accounts. This model stops where that one starts and adds what a transfer
//! does with accounts Anchor left unchecked: the handler reads them only when
//! it moves funds. Recovered from `evidence/original/pump/deployed.so` and
//! checked against it on LiteSVM by
//! `tests/test_collect_account_admission_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.
//!
//! Admission runs in two stages. Typed fields load in field order:
//! `quote_mint`, then the three program slots. The constraints then run in
//! field order, seeds before `mut` in one slot, with `event_authority` last.
//! `program` is not checked at all: a wrong one only fails the event self-CPI,
//! so a call that emits no event succeeds with it.
//!
//! Unconfirmed (미확인, outside the checked inputs): Token-2022 accounts, a
//! `quote_mint` owned by Token-2022 with `quote_token_program` set to it, and a
//! token account between 4 and 165 bytes.

pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const NOT_INITIALIZED: u32 = 3012;
/// SPL Token codes, from the transfer.
pub const TOKEN_MINT_MISMATCH: u32 = 3;
pub const TOKEN_OWNER_MISMATCH: u32 = 4;
pub const TOKEN_FROZEN: u32 = 17;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Handler {
    V1,
    /// `collect_creator_fee_v2` with the WSOL mint.
    V2Native,
    /// `collect_creator_fee_v2` with any other mint.
    V2Token,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct AddressSlot {
    pub wrong_address: bool,
    pub read_only: bool,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum MintSlot {
    #[default]
    Expected,
    Missing,
    WrongOwner,
    /// Four bytes of data.
    Short,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum TokenProgramSlot {
    #[default]
    Expected,
    /// Token-2022, so the token account seeds no longer match.
    OtherInterface,
    Invalid,
}

/// A native vault as the System program sees it at the transfer.
#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum VaultShape {
    #[default]
    SystemOwned,
    ForeignOwner,
    HoldsData,
}

/// A token account's bytes. The admission never reads them.
#[derive(Clone, Copy, Default, Debug)]
pub struct TokenState {
    pub foreign_owner: bool,
    /// Missing, or four bytes.
    pub unreadable: bool,
    pub wrong_mint: bool,
    pub wrong_authority: bool,
    pub frozen: bool,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct Request {
    pub creator_read_only: bool,
    pub creator_token: AddressSlot,
    pub vault: AddressSlot,
    pub vault_token: AddressSlot,
    pub mint_wrong_address: bool,
    pub mint: MintSlot,
    pub token_program: TokenProgramSlot,
    pub associated_program_ok: bool,
    pub system_program_ok: bool,
    pub event_authority_ok: bool,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    Code(u32),
    InvalidAccountData,
    /// A native vault the System program cannot debit.
    ExternalLamportSpend,
    /// A native vault holding data.
    InvalidArgument,
    /// The token account's owner is not the token program.
    ExternalDataModified,
    /// The event self-CPI, with no Pump account to invoke.
    MissingAccount,
}

fn code(c: u32) -> Stop {
    Stop::Code(c)
}

/// Fields load first. Handler `V1` has only `system_program` here.
fn load_stage(handler: Handler, r: &Request) -> Result<(), Stop> {
    if handler != Handler::V1 {
        match r.mint {
            MintSlot::Expected => {}
            MintSlot::Missing => return Err(code(NOT_INITIALIZED)),
            MintSlot::WrongOwner => return Err(code(OWNED_BY_WRONG_PROGRAM)),
            MintSlot::Short => return Err(Stop::InvalidAccountData),
        }
        if r.token_program == TokenProgramSlot::Invalid || !r.associated_program_ok {
            return Err(code(INVALID_PROGRAM_ID));
        }
    }
    if !r.system_program_ok {
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

fn constraint_stage(handler: Handler, r: &Request) -> Result<(), Stop> {
    if r.creator_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    let token_seed = r.mint_wrong_address || r.token_program == TokenProgramSlot::OtherInterface;
    let v2 = handler != Handler::V1;
    if v2 {
        seeded(&r.creator_token, token_seed)?;
    }
    seeded(&r.vault, false)?;
    if v2 {
        seeded(&r.vault_token, token_seed)?;
    }
    if !r.event_authority_ok {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}

pub fn admit(handler: Handler, r: &Request) -> Result<(), Stop> {
    load_stage(handler, r)?;
    constraint_stage(handler, r)
}

/// The System program's refusal of the vault, once the handler moves lamports.
pub fn native_transfer(vault: VaultShape) -> Result<(), Stop> {
    match vault {
        VaultShape::SystemOwned => Ok(()),
        VaultShape::ForeignOwner => Err(Stop::ExternalLamportSpend),
        VaultShape::HoldsData => Err(Stop::InvalidArgument),
    }
}

/// SPL Token's refusal, once the handler moves a non-zero balance. The source
/// has to be readable before that, because the handler reads its amount.
pub fn token_transfer(source: &TokenState, destination: &TokenState) -> Result<(), Stop> {
    if source.unreadable || destination.unreadable {
        return Err(Stop::InvalidAccountData);
    }
    if source.frozen || destination.frozen {
        return Err(code(TOKEN_FROZEN));
    }
    if source.wrong_mint != destination.wrong_mint || source.wrong_mint {
        return Err(code(TOKEN_MINT_MISMATCH));
    }
    if source.wrong_authority {
        return Err(code(TOKEN_OWNER_MISMATCH));
    }
    if source.foreign_owner || destination.foreign_owner {
        return Err(Stop::ExternalDataModified);
    }
    Ok(())
}
