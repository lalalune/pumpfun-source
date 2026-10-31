//! Pure model of Pump `distribute_creator_fees_v2` on a Token-2022 quote mint,
//! on top of the admission rules in `creator_fee_distribution_quote.rs`, as
//! observed on the captured program (`evidence/original/pump/deployed.so`).
//!
//! Observed rules, checked by
//! `tests/test_creator_fee_distribution_token2022_captured.py`:
//! * Every account and share check runs first, for all shareholders, exactly
//!   as on an SPL quote. Only then do the ATA creations and transfers run, one
//!   shareholder at a time and in configured order.
//! * Each share is still `vault_tokens * bps / 10000`, floored, and the vault
//!   ATA loses that gross amount. `distributed` in the event and return data is
//!   the gross sum. The shareholder gets it less the transfer fee, which stays
//!   withheld on the shareholder's ATA.
//! * An ATA created at the payer's cost follows the mint: 170 bytes, plus 12
//!   with a transfer fee, 5 with a hook and 4 with pausable, at
//!   `(128 + size) * 6960` lamports.
//! * A zero-token share still gets its ATA created, but never reaches the token
//!   program's transfer, so none of its failures apply.
//!
//! This is a behavioural model of matching outcomes on synthetic inputs, not a
//! byte-identity or source-recovery claim. Unconfirmed (미확인, outside the
//! checked inputs): extensions other than the ones named here, a hook program
//! that is really invoked, and interest-bearing or scaled-amount mints.

use crate::creator_fee_distribution_quote::{self as quote, Ata, Failure, QuoteDistribution, Shareholder};

pub const TOKEN_INSUFFICIENT_FUNDS: u32 = quote::TOKEN_INSUFFICIENT_FUNDS;
pub const TOKEN_MINT_MISMATCH: u32 = 3;
pub const TOKEN_OWNER_MISMATCH: u32 = 4;
pub const TOKEN_INVALID_STATE: u32 = 13;
pub const TOKEN_ACCOUNT_FROZEN: u32 = 17;
pub const TOKEN_NO_MEMO: u32 = 36;
pub const TOKEN_NON_TRANSFERABLE: u32 = 37;
pub const TOKEN_CPI_GUARD_TRANSFER: u32 = 42;
pub const TOKEN_MINT_PAUSED: u32 = 67;

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

#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub struct Vault {
    pub frozen: bool,
    pub owner_mismatch: bool,
    pub mint_mismatch: bool,
    pub cpi_guard: bool,
    pub non_transferable: bool,
}

/// State of a shareholder's existing ATA.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub struct Holding {
    pub frozen: bool,
    pub mint_mismatch: bool,
    pub memo_required: bool,
    pub no_fee_extension: bool,
}

#[derive(Clone, Debug)]
pub struct Distribution {
    pub base: QuoteDistribution,
    pub vault: Vault,
    pub holdings: Vec<Holding>,
    pub fee: Option<TransferFee>,
    pub epoch: u64,
    pub hook_set: bool,
    pub paused: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Default)]
pub struct Distributed {
    pub transfers: Vec<u64>,
    pub withheld: Vec<u64>,
    pub distributed: u64,
    pub ata_rent: u64,
}

fn ata_rent(d: &Distribution) -> u64 {
    let extensions = if d.fee.is_some() { 12 } else { 0 } + if d.hook_set { 5 } else { 0 } + if d.paused { 4 } else { 0 };
    (128 + 170 + extensions) * 6960
}

fn share(source: u64, shareholder: &Shareholder) -> u64 {
    (u128::from(source) * u128::from(shareholder.bps) / 10_000) as u64
}

/// The token program's own checks for one transfer, in failing order.
fn transfer(d: &Distribution, left: u64, amount: u64, destination: &Holding) -> Result<u64, Failure> {
    let code = |code| Err(Failure::Custom(code));
    if d.vault.frozen {
        return code(TOKEN_ACCOUNT_FROZEN);
    }
    if left < amount {
        return code(TOKEN_INSUFFICIENT_FUNDS);
    }
    if d.vault.non_transferable {
        return code(TOKEN_NON_TRANSFERABLE);
    }
    if d.vault.mint_mismatch {
        return code(TOKEN_MINT_MISMATCH);
    }
    if d.paused {
        return code(TOKEN_MINT_PAUSED);
    }
    if d.vault.owner_mismatch {
        return code(TOKEN_OWNER_MISMATCH);
    }
    if d.vault.cpi_guard {
        return code(TOKEN_CPI_GUARD_TRANSFER);
    }
    if destination.frozen {
        return code(TOKEN_ACCOUNT_FROZEN);
    }
    if destination.mint_mismatch {
        return code(TOKEN_MINT_MISMATCH);
    }
    if destination.memo_required {
        return code(TOKEN_NO_MEMO);
    }
    let withheld = d.fee.map_or(0, |fee| fee.withheld(d.epoch, amount));
    if withheld != 0 && destination.no_fee_extension {
        return code(TOKEN_INVALID_STATE);
    }
    if d.hook_set {
        return Err(Failure::InvalidAccountData);
    }
    Ok(withheld)
}

pub fn distribute(d: &Distribution) -> Result<Distributed, Failure> {
    // An over-allocated list only fails in the token program below, so the
    // transfers before it still decide which failure comes first.
    match quote::distribute(&d.base) {
        Ok(_) | Err(Failure::Custom(TOKEN_INSUFFICIENT_FUNDS)) => {}
        Err(failure) => return Err(failure),
    }
    let source = d.base.vault_tokens.ok_or(Failure::InvalidAccountData)?;
    let mut out = Distributed::default();
    let mut left = source;
    for (shareholder, holding) in d.base.shareholders.iter().zip(&d.holdings) {
        let amount = share(source, shareholder);
        let created = shareholder.ata == Some(Ata::Absent);
        let destination = if created { Holding::default() } else { *holding };
        if created {
            out.ata_rent += ata_rent(d);
        }
        let kept = if amount == 0 { 0 } else { transfer(d, left, amount, &destination)? };
        out.withheld.push(kept);
        out.transfers.push(amount);
        left -= amount;
        out.distributed += amount;
    }
    Ok(out)
}
