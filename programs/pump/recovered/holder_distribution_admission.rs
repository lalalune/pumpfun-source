//! Captured account admission of Pump `distribute_fee_to_holders`: which accounts
//! it refuses, with which code, and which refusal wins when several are wrong.
//!
//! `holder_distribution.rs` and `holder_distribution_token.rs` take a few flags for
//! the signature, the authority, the PDA and the source's stored fields, and leave
//! the other accounts out. This model states the whole order, on the SOL path, on a
//! wrapped-SOL source and on an SPL Token quote. Recovered from
//! `evidence/original/pump/deployed.so` and checked against it on LiteSVM by
//! `tests/test_holder_distribution_admission_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.
//!
//! Admission runs in two stages. Accounts load in field order. `mint` and
//! `holder_rewards` are unchecked, so neither loads, and the optional
//! `holder_rewards_token_account` is absent when the slot holds the program's own
//! key. The constraints then run in field order. That slot has no address rule: any
//! account with the right stored fields passes. `holder_rewards` is only written,
//! so its bytes show at the first lamport payout and not before.
//!
//! The event CPI needs the program among the transaction's accounts. A wrong
//! `program` slot therefore fails at the end only when nothing else holds that
//! key, which is when a source account fills the optional slot.
//!
//! Unconfirmed (미확인, outside the checked inputs): Token-2022 quotes, and accounts
//! between 4 bytes and their full length.

pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const CONSTRAINT_TOKEN_MINT: u32 = 2014;
pub const CONSTRAINT_TOKEN_OWNER: u32 = 2015;
pub const CONSTRAINT_TOKEN_PROGRAM: u32 = 2021;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
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

/// The optional `holder_rewards_token_account`.
#[derive(Clone, Copy, Default, Debug)]
pub struct SourceSlot {
    /// The slot holds an account, not the program's own key.
    pub present: bool,
    pub load: Load,
    pub read_only: bool,
    pub wrong_authority: bool,
    pub wrong_mint: bool,
    /// Its owner is not `quote_token_program`.
    pub wrong_program: bool,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct Request {
    pub global: Load,
    pub global_wrong_address: bool,
    pub authority_unsigned: bool,
    pub authority_wrong: bool,
    pub authority_read_only: bool,
    /// Another mint key, or another key in `holder_rewards`.
    pub rewards_wrong_address: bool,
    pub rewards_read_only: bool,
    pub source: SourceSlot,
    pub quote_mint: Load,
    pub quote_token_program_wrong: bool,
    pub associated_program_wrong: bool,
    pub system_program_wrong: bool,
    pub event_authority_wrong: bool,
}

/// `holder_rewards` as the first lamport payout finds it.
#[derive(Clone, Copy, Default, Debug)]
pub struct Rewards {
    pub foreign_owner: bool,
    pub has_data: bool,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    Code(u32),
    InvalidAccountData,
    InvalidArgument,
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

/// `InterfaceAccount<T>`.
fn load_decoded(load: Load) -> Result<(), Stop> {
    load_common(load)?;
    if load == Load::Stored {
        Ok(())
    } else {
        Err(Stop::InvalidAccountData)
    }
}

fn load_stage(r: &Request) -> Result<(), Stop> {
    load_typed(r.global)?;
    if r.authority_unsigned {
        return Err(code(NOT_SIGNER));
    }
    if r.source.present {
        load_decoded(r.source.load)?;
    }
    load_decoded(r.quote_mint)?;
    if r.quote_token_program_wrong || r.associated_program_wrong || r.system_program_wrong {
        return Err(code(INVALID_PROGRAM_ID));
    }
    Ok(())
}

fn constraint_stage(r: &Request) -> Result<(), Stop> {
    if r.global_wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.authority_wrong {
        return Err(code(NOT_AUTHORIZED));
    }
    if r.authority_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.rewards_wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.rewards_read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.source.present {
        if r.source.read_only {
            return Err(code(CONSTRAINT_MUT));
        }
        if r.source.wrong_authority {
            return Err(code(CONSTRAINT_TOKEN_OWNER));
        }
        if r.source.wrong_mint {
            return Err(code(CONSTRAINT_TOKEN_MINT));
        }
        if r.source.wrong_program {
            return Err(code(CONSTRAINT_TOKEN_PROGRAM));
        }
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

/// The refusal of the first lamport payout.
pub fn first_payout(rewards: &Rewards) -> Result<(), Stop> {
    if rewards.has_data {
        return Err(Stop::InvalidArgument);
    }
    if rewards.foreign_owner {
        return Err(Stop::ExternalLamportSpend);
    }
    Ok(())
}
