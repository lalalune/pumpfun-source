//! Pure model of Pump `collect_creator_fee_v2` on a Token-2022 quote mint, on
//! top of the creator rules in `creator_fee_collect.rs`, as observed on the
//! captured program (`evidence/original/pump/deployed.so`).
//!
//! Observed rules, checked by
//! `tests/test_creator_fee_collect_token2022_captured.py`:
//! * Mint owner (3007) and token program (3008) fail first, then the ATA
//!   addresses (2006), then the creator rules: a creator owned by Pump Fees
//!   fails with 6050 and an executable one returns Ok with no transfer.
//! * The vault ATA is parsed as a token account by Pump itself, whichever
//!   program owns it: a missing or short account fails with InvalidAccountData
//!   and an uninitialized one with UninitializedAccount.
//!   A zero balance returns Ok with no event, before the creator ATA is seen.
//! * The whole balance leaves the vault ATA and the event carries it. The
//!   creator ATA receives it less the transfer fee, which stays withheld.
//! * Failures of the token transfer follow the order in `transfer`.
//!
//! This is a behavioural model of matching outcomes on synthetic inputs, not a
//! byte-identity or source-recovery claim. Unconfirmed (미확인, outside the
//! checked inputs): extensions other than the ones named here, a hook program
//! that is really invoked, and interest-bearing or scaled-amount mints.

use crate::creator_fee_collect::{self, Collect, CollectError, Collected, Quote};

pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const TOKEN_MINT_MISMATCH: u32 = 3;
pub const TOKEN_OWNER_MISMATCH: u32 = 4;
pub const TOKEN_INVALID_STATE: u32 = 13;
pub const TOKEN_ACCOUNT_FROZEN: u32 = 17;
pub const TOKEN_NO_MEMO: u32 = 36;
pub const TOKEN_NON_TRANSFERABLE: u32 = 37;
pub const TOKEN_CPI_GUARD_TRANSFER: u32 = 42;
pub const TOKEN_MINT_PAUSED: u32 = 67;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TokenProgram {
    Token2022,
    Spl,
    Other,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MintOwner {
    Token2022,
    Spl,
    Other,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TransferFee {
    pub older_bps: u16,
    pub older_max: u64,
    pub newer_epoch: u64,
    pub newer_bps: u16,
    pub newer_max: u64,
}

impl TransferFee {
    pub fn withheld(&self, epoch: u64, amount: u64) -> u64 {
        let (bps, max) = if epoch >= self.newer_epoch {
            (self.newer_bps, self.newer_max)
        } else {
            (self.older_bps, self.older_max)
        };
        let fee = (u128::from(amount) * u128::from(bps)).div_ceil(10_000);
        fee.min(u128::from(max)) as u64
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Mint {
    pub owner: MintOwner,
    pub fee: Option<TransferFee>,
    pub hook_set: bool,
    pub paused: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Holding {
    pub balance: u64,
    pub frozen: bool,
    pub fee_extension: bool,
    pub owner_matches: bool,
    pub mint_matches: bool,
    pub memo_required: bool,
    pub cpi_guard: bool,
    pub non_transferable: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Ata {
    Missing,
    /// Well-formed data under the other token program.
    WrongProgram(Holding),
    Truncated,
    Uninitialized,
    Held(Holding),
}

pub struct CollectToken2022 {
    pub creator_owned_by_fees: bool,
    pub creator_executable: bool,
    pub token_program: TokenProgram,
    pub mint: Mint,
    pub epoch: u64,
    pub addresses_ok: bool,
    pub vault_ata: Ata,
    pub creator_ata: Ata,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    InvalidAccountData,
    UninitializedAccount,
    IncorrectProgramId,
}

#[derive(Debug, Default, PartialEq, Eq)]
pub struct Collected2022 {
    pub tokens: u64,
    pub withheld: u64,
    pub event: bool,
}

/// Pump reads the balance itself, before any token program is involved.
fn read_vault(ata: &Ata) -> Result<Holding, Stop> {
    match ata {
        Ata::Missing | Ata::Truncated => Err(Stop::InvalidAccountData),
        Ata::Uninitialized => Err(Stop::UninitializedAccount),
        Ata::WrongProgram(held) | Ata::Held(held) => Ok(*held),
    }
}

fn transfer(c: &CollectToken2022, source: &Holding, amount: u64) -> Result<u64, Stop> {
    // Token-2022 refuses an account it does not own before anything else.
    if c.token_program == TokenProgram::Token2022
        && (matches!(c.vault_ata, Ata::WrongProgram(_)) || matches!(c.creator_ata, Ata::WrongProgram(_) | Ata::Missing))
    {
        return Err(Stop::IncorrectProgramId);
    }
    if c.token_program == TokenProgram::Spl && (c.mint.fee.is_some() || c.mint.hook_set || c.mint.paused) {
        return Err(Stop::InvalidAccountData);
    }
    if source.frozen {
        return Err(Stop::Code(TOKEN_ACCOUNT_FROZEN));
    }
    if source.non_transferable {
        return Err(Stop::Code(TOKEN_NON_TRANSFERABLE));
    }
    if c.token_program == TokenProgram::Token2022 && c.mint.owner != MintOwner::Token2022 {
        return Err(Stop::IncorrectProgramId);
    }
    if !source.mint_matches {
        return Err(Stop::Code(TOKEN_MINT_MISMATCH));
    }
    if c.mint.paused {
        return Err(Stop::Code(TOKEN_MINT_PAUSED));
    }
    if !source.owner_matches {
        return Err(Stop::Code(TOKEN_OWNER_MISMATCH));
    }
    if source.cpi_guard {
        return Err(Stop::Code(TOKEN_CPI_GUARD_TRANSFER));
    }
    let destination = match &c.creator_ata {
        Ata::Missing | Ata::Truncated => return Err(Stop::InvalidAccountData),
        Ata::WrongProgram(_) => return Err(Stop::IncorrectProgramId),
        Ata::Uninitialized => return Err(Stop::UninitializedAccount),
        Ata::Held(held) => held,
    };
    if destination.frozen {
        return Err(Stop::Code(TOKEN_ACCOUNT_FROZEN));
    }
    if !destination.mint_matches {
        return Err(Stop::Code(TOKEN_MINT_MISMATCH));
    }
    if destination.memo_required {
        return Err(Stop::Code(TOKEN_NO_MEMO));
    }
    let withheld = c.mint.fee.map_or(0, |fee| fee.withheld(c.epoch, amount));
    if withheld != 0 && !destination.fee_extension {
        return Err(Stop::Code(TOKEN_INVALID_STATE));
    }
    if c.mint.hook_set {
        return Err(Stop::InvalidAccountData);
    }
    Ok(withheld)
}

pub fn collect(c: &CollectToken2022) -> Result<Collected2022, Stop> {
    if c.mint.owner == MintOwner::Other {
        return Err(Stop::Code(ACCOUNT_OWNED_BY_WRONG_PROGRAM));
    }
    if c.token_program == TokenProgram::Other {
        return Err(Stop::Code(INVALID_PROGRAM_ID));
    }
    if !c.addresses_ok {
        return Err(Stop::Code(CONSTRAINT_SEEDS));
    }
    // The creator rules run before the vault ATA is read; the amount that
    // decides the event comes from the ATA below.
    let gate = creator_fee_collect::collect(&Collect {
        creator_owned_by_fees: c.creator_owned_by_fees,
        creator_executable: c.creator_executable,
        creator_lamports: 0,
        creator_data_len: 0,
        vault_lamports: 0,
        quote: Quote::Spl { vault_tokens: Some(1), creator_ata_exists: true },
    });
    match gate {
        Err(CollectError::Custom(code)) => return Err(Stop::Code(code)),
        Err(other) => unreachable!("not on the token path: {other:?}"),
        Ok(Collected { event: false, .. }) => return Ok(Collected2022::default()),
        Ok(_) => {}
    }
    let source = read_vault(&c.vault_ata)?;
    if source.balance == 0 {
        return Ok(Collected2022::default());
    }
    let withheld = transfer(c, &source, source.balance)?;
    Ok(Collected2022 { tokens: source.balance, withheld, event: true })
}
