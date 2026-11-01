//! Captured account admission of Pump `claim_cashback_v2`: which accounts it
//! refuses, with which code, which refusal wins when several are wrong, and how
//! far the token route reads the accounts Anchor leaves unchecked.
//!
//! `claim_cashback_v2.rs` starts after the Anchor checks and takes readable
//! accounts. This model stops where that one starts. Recovered from
//! `evidence/original/pump/deployed.so` and checked against it on LiteSVM by
//! `tests/test_claim_cashback_v2_admission_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.
//!
//! Admission runs in two stages. Typed fields load in field order, the
//! accumulator first and then the three program slots. The constraints then run
//! in field order. `quote_mint` and `quote_token_program` are unchecked, but the
//! accumulator's token account derives from them, so a wrong one fails those
//! seeds on both routes. `associated_quote_user` has no address check at all.
//!
//! Unconfirmed (미확인, outside the checked inputs): Token-2022 accounts, and
//! token accounts or mints between 4 and their full length.

pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const NOT_INITIALIZED: u32 = 3012;
pub const ACCOUNT_TYPE_NOT_SUPPORTED: u32 = 6010;
pub const INVALID_CASHBACK_RECIPIENT: u32 = 6076;
/// SPL Token codes, from the transfer.
pub const TOKEN_MINT_MISMATCH: u32 = 3;
pub const TOKEN_OWNER_MISMATCH: u32 = 4;
pub const TOKEN_FROZEN: u32 = 17;

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum AccumulatorLoad {
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

/// A token account's bytes as passed.
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

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum MintState {
    #[default]
    Readable,
    Missing,
    /// Four bytes.
    Short,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct Request {
    pub user_read_only: bool,
    pub accumulator: AddressSlot,
    pub accumulator_load: AccumulatorLoad,
    pub mint_wrong_address: bool,
    pub token_program_wrong: bool,
    pub associated_program_wrong: bool,
    pub accumulator_token: AddressSlot,
    pub user_token_read_only: bool,
    pub system_program_wrong: bool,
    pub event_authority_wrong: bool,
    pub program_wrong: bool,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    Code(u32),
    InvalidAccountData,
    /// The source's owner is not the token program.
    ExternalDataModified,
}

/// How the token route ends once admission has passed.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Route {
    /// Nothing to claim: no transfer and no event.
    Empty,
    Transfer,
    Stop(Stop),
}

fn code(c: u32) -> Stop {
    Stop::Code(c)
}

fn load_stage(r: &Request) -> Result<(), Stop> {
    match r.accumulator_load {
        AccumulatorLoad::Stored => {}
        AccumulatorLoad::Missing => return Err(code(NOT_INITIALIZED)),
        AccumulatorLoad::WrongOwner => return Err(code(OWNED_BY_WRONG_PROGRAM)),
        AccumulatorLoad::Short => return Err(code(DISCRIMINATOR_NOT_FOUND)),
        AccumulatorLoad::BadDiscriminator => return Err(code(DISCRIMINATOR_MISMATCH)),
        AccumulatorLoad::Truncated => return Err(code(DID_NOT_DESERIALIZE)),
    }
    if r.associated_program_wrong || r.system_program_wrong || r.program_wrong {
        return Err(code(INVALID_PROGRAM_ID));
    }
    Ok(())
}

fn constraint_stage(r: &Request) -> Result<(), Stop> {
    if r.user_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.accumulator.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.accumulator.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.accumulator_token.wrong_address || r.mint_wrong_address || r.token_program_wrong {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.accumulator_token.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.user_token_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.event_authority_wrong {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}

pub fn admit(r: &Request) -> Result<(), Stop> {
    load_stage(r)?;
    constraint_stage(r)
}

/// The token route after admission, in order. The handler checks the mint's
/// owner, reads the accumulator's balance, reads the recipient, and only then
/// reads the mint's data and calls SPL Token. `InvalidQuoteTokenProgram` (6064)
/// is not in these inputs: `claim_cashback_v2.rs` reaches it with a token account
/// derived from the wrong program, and here that slot keeps the expected one.
pub fn token_route(mint: MintState, source: &TokenState, destination: &TokenState, balance_is_zero: bool) -> Route {
    if mint == MintState::Missing {
        return Route::Stop(code(ACCOUNT_TYPE_NOT_SUPPORTED));
    }
    if source.missing {
        return Route::Empty;
    }
    if source.short {
        return Route::Stop(Stop::InvalidAccountData);
    }
    if balance_is_zero {
        return Route::Empty;
    }
    if destination.missing || destination.foreign_owner {
        return Route::Stop(code(ACCOUNT_TYPE_NOT_SUPPORTED));
    }
    if destination.short {
        return Route::Stop(Stop::InvalidAccountData);
    }
    if destination.wrong_authority {
        return Route::Stop(code(INVALID_CASHBACK_RECIPIENT));
    }
    // A short mint gets this far: only its owner was checked before.
    if mint == MintState::Short {
        return Route::Stop(Stop::InvalidAccountData);
    }
    if source.frozen || destination.frozen {
        return Route::Stop(code(TOKEN_FROZEN));
    }
    if source.wrong_mint != destination.wrong_mint || source.wrong_mint {
        return Route::Stop(code(TOKEN_MINT_MISMATCH));
    }
    if source.wrong_authority {
        return Route::Stop(code(TOKEN_OWNER_MISMATCH));
    }
    if source.foreign_owner {
        return Route::Stop(Stop::ExternalDataModified);
    }
    Route::Transfer
}
