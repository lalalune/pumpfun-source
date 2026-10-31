//! Pure model of Pump `distribute_creator_fees_v2` when the Token-2022 quote
//! mint itself carries `NonTransferable` or `DefaultAccountState = Frozen`,
//! on top of `creator_fee_distribution_token2022.rs`, whose own header leaves
//! both unconfirmed. Checked against the captured program
//! (`evidence/original/pump/deployed.so`) on LiteSVM by
//! `tests/test_creator_fee_distribution_mint_extensions_captured.py`.
//! Not linked into the SBF crate. This is not a byte-identity claim.
//!
//! What the mint extensions do, as observed:
//! * `NonTransferable` on the mint blocks nothing by itself: the token
//!   program refuses transfers out of an account carrying the
//!   `NonTransferableAccount` extension, and never refuses a transfer into
//!   one. The mint extension's force is on creation — every account the
//!   associated-token program creates for this mint carries that extension
//!   (and `ImmutableOwner`, like any created account here), so a created
//!   shareholder account is 174 bytes and a realistic vault, created the
//!   same way, refuses every distribution transfer with error 37 at the
//!   base model's source position.
//! * `DefaultAccountState = Frozen` touches only accounts created after it:
//!   a shareholder ATA created by the distribution starts frozen, so its
//!   transfer fails with error 17 at that shareholder's turn, in configured
//!   order. Existing accounts keep the state they already have, and a
//!   zero-token share still creates its (frozen) account and succeeds.
//!
//! Unconfirmed (미확인, outside the checked inputs): the two extensions
//! combined with a transfer hook that really runs, and interest-bearing or
//! scaled-amount mints (the base packets' open items, unchanged).

use crate::creator_fee_distribution_quote::{self as quote, Ata, Failure};
use crate::creator_fee_distribution_token2022::{self as base, Distributed, Distribution, Holding};

#[derive(Clone, Debug)]
pub struct MintDistribution {
    pub base: Distribution,
    /// The mint carries `NonTransferable`. The fixture's vault and existing
    /// accounts then carry the account extension too — the base model's
    /// `vault.non_transferable` — because that is the only account set the
    /// associated-token program produces for such a mint; a mint-only state
    /// is a separate input shape the test also runs.
    pub mint_non_transferable: bool,
    /// The mint carries `DefaultAccountState = Frozen`.
    pub mint_default_frozen: bool,
}

/// The base model's transfer checks, repeated because they are private to
/// it; the only change is the state of a created destination, which the
/// caller folds into `destination`. `run` below is guarded against the base
/// model whenever neither mint extension applies.
fn transfer(d: &Distribution, left: u64, amount: u64, destination: &Holding) -> Result<u64, Failure> {
    let code = |code| Err(Failure::Custom(code));
    if d.vault.frozen {
        return code(base::TOKEN_ACCOUNT_FROZEN);
    }
    if left < amount {
        return code(base::TOKEN_INSUFFICIENT_FUNDS);
    }
    if d.vault.non_transferable {
        return code(base::TOKEN_NON_TRANSFERABLE);
    }
    if d.vault.mint_mismatch {
        return code(base::TOKEN_MINT_MISMATCH);
    }
    if d.paused {
        return code(base::TOKEN_MINT_PAUSED);
    }
    if d.vault.owner_mismatch {
        return code(base::TOKEN_OWNER_MISMATCH);
    }
    if d.vault.cpi_guard {
        return code(base::TOKEN_CPI_GUARD_TRANSFER);
    }
    if destination.frozen {
        return code(base::TOKEN_ACCOUNT_FROZEN);
    }
    if destination.mint_mismatch {
        return code(base::TOKEN_MINT_MISMATCH);
    }
    if destination.memo_required {
        return code(base::TOKEN_NO_MEMO);
    }
    let withheld = d.fee.map_or(0, |fee| fee.withheld(d.epoch, amount));
    if withheld != 0 && destination.no_fee_extension {
        return code(base::TOKEN_INVALID_STATE);
    }
    if d.hook_set {
        return Err(Failure::InvalidAccountData);
    }
    Ok(withheld)
}

fn ata_rent(d: &MintDistribution) -> u64 {
    // The base model's created-account size, plus 4 bytes when the mint is
    // non-transferable: the `NonTransferableAccount` extension a created
    // account then carries.
    let b = &d.base;
    let extensions = if b.fee.is_some() { 12 } else { 0 } + if b.hook_set { 5 } else { 0 } + if b.paused { 4 } else { 0 }
        + if d.mint_non_transferable { 4 } else { 0 };
    (128 + 170 + extensions) * 6960
}

fn share(source: u64, shareholder: &quote::Shareholder) -> u64 {
    (u128::from(source) * u128::from(shareholder.bps) / 10_000) as u64
}

pub fn distribute(d: &MintDistribution) -> Result<Distributed, Failure> {
    if !d.mint_non_transferable && !d.mint_default_frozen {
        return base::distribute(&d.base);
    }
    // The loop of the base model, with created destinations carrying the
    // mint's default state and creation priced by the extended size.
    match quote::distribute(&d.base.base) {
        Ok(_) | Err(Failure::Custom(base::TOKEN_INSUFFICIENT_FUNDS)) => {}
        Err(failure) => return Err(failure),
    }
    let b = &d.base;
    let source = b.base.vault_tokens.ok_or(Failure::InvalidAccountData)?;
    let mut out = Distributed::default();
    let mut left = source;
    for (shareholder, holding) in b.base.shareholders.iter().zip(&b.holdings) {
        let amount = share(source, shareholder);
        let created = shareholder.ata == Some(Ata::Absent);
        let destination = if created {
            Holding { frozen: d.mint_default_frozen, ..Holding::default() }
        } else {
            *holding
        };
        if created {
            out.ata_rent += ata_rent(d);
        }
        let kept = if amount == 0 { 0 } else { transfer(b, left, amount, &destination)? };
        out.withheld.push(kept);
        out.transfers.push(amount);
        left -= amount;
        out.distributed += amount;
    }
    Ok(out)
}
