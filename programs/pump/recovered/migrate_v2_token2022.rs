//! Captured behavior of Pump `migrate_v2` on a Token-2022 quote mint, on top of
//! the rules in `migrate_v2.rs`: the quote `create_pool` receives after the
//! transfer fee, the token failures of the move out of the curve, the accounts
//! created for the pool, and the harvest and close of a pool authority quote
//! account created here.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured SPL
//! Token, Token-2022 and Associated Token programs by
//! `tests/test_migrate_v2_token2022_captured.py`, with the no-op pump_amm of
//! `tests/test_migrate_v2_captured.py`. Not linked into the SBF crate. This is
//! not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): a close with tokens that a
//! real pump_amm has taken, a Token-2022 base mint, extensions other than the
//! ones named here, a hook program that is really invoked, a mint withheld total
//! that overflows, interest-bearing or scaled-amount mints, and
//! `UnsupportedQuoteMint` on the boost path: every malformed mint tried fails
//! earlier, at the load or at the account creation.

use crate::migrate_v2::{self, MigrateV2, Outcome, Stop as BaseStop};

pub const OVERFLOW: u32 = migrate_v2::OVERFLOW;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: u32 = migrate_v2::NOT_ENOUGH_REMAINING_ACCOUNTS;
pub const QUOTE_MINT_NOT_WRITABLE: u32 = 6110;
pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;
pub const TOKEN_NON_NATIVE_HAS_BALANCE: u32 = 11;
pub const TOKEN_INVALID_STATE: u32 = 13;
pub const TOKEN_ACCOUNT_FROZEN: u32 = 17;
pub const TOKEN_NO_MEMO: u32 = 36;
pub const TOKEN_NON_TRANSFERABLE: u32 = 37;
pub const TOKEN_CPI_GUARD_TRANSFER: u32 = 42;
pub const TOKEN_MINT_PAUSED: u32 = 67;

const SPL_ATA_SIZE: u64 = 165;
/// A Token-2022 account: the SPL layout, the type byte, ImmutableOwner.
const ATA_SIZE: u64 = 170;

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
    /// The mint is owned by `quote_token_program`.
    pub owner_matches_program: bool,
    pub spl_program: bool,
    /// Refused by the Anchor load (padding, length or account type).
    pub malformed_layout: bool,
    /// Past the load, but its extensions do not parse in the token program.
    pub malformed_extensions: bool,
    pub fee: Option<TransferFee>,
    pub hook_set: bool,
    pub paused: bool,
    pub non_transferable: bool,
    pub writable: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Holding {
    pub frozen: bool,
    pub fee_extension: bool,
    pub memo_required: bool,
    pub cpi_guard: bool,
    pub non_transferable: bool,
    pub hook_extension: bool,
}

pub struct MigrateToken2022 {
    /// `quote_vault` stays `u64::MAX`: the balance below is applied here, in
    /// the order the token program checks it.
    pub base: MigrateV2,
    pub vault_balance: u64,
    pub mint: Mint,
    pub epoch: u64,
    pub vault: Holding,
    /// `None`: the pool authority's quote account does not exist yet.
    pub pool_authority: Option<Holding>,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    Base(BaseStop),
    InvalidAccountData,
    IncorrectProgramId,
    MissingAccount,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Moved {
    pub init_boost: bool,
    pub curve_lamports: u64,
    /// Left in the curve's quote account.
    pub vault: u64,
    /// The gross amount that left the vault, and what the transfer fee kept.
    pub moved: u64,
    pub withheld: u64,
    /// The quote `create_pool` and the event carry.
    pub quote: u64,
    /// The pool authority's account was created here, and so closed again.
    pub closed: bool,
    /// Size of the pool's quote account.
    pub pool_quote_size: u64,
    /// Harvested from the closed account into the mint.
    pub harvested: u64,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Migrated {
    AlreadyMigrated { curve_lamports: u64 },
    Moved(Moved),
}

fn created_size(mint: &Mint) -> u64 {
    if mint.spl_program {
        return SPL_ATA_SIZE;
    }
    let mut size = ATA_SIZE;
    if mint.fee.is_some() {
        size += 12;
    }
    if mint.hook_set {
        size += 5;
    }
    if mint.paused {
        size += 4;
    }
    if mint.non_transferable {
        size += 4;
    }
    size
}

/// The move out of the curve's quote account; 0 skips the CPI.
fn transfer(m: &MigrateToken2022, destination: &Holding, balance: u64, amount: u64) -> Result<u64, Stop> {
    if amount == 0 {
        return Ok(0);
    }
    if m.vault.frozen {
        return Err(Stop::Code(TOKEN_ACCOUNT_FROZEN));
    }
    if balance < amount {
        return Err(Stop::Code(TOKEN_INSUFFICIENT_FUNDS));
    }
    if m.vault.non_transferable {
        return Err(Stop::Code(TOKEN_NON_TRANSFERABLE));
    }
    if m.mint.paused {
        return Err(Stop::Code(TOKEN_MINT_PAUSED));
    }
    if m.vault.cpi_guard {
        return Err(Stop::Code(TOKEN_CPI_GUARD_TRANSFER));
    }
    if destination.frozen {
        return Err(Stop::Code(TOKEN_ACCOUNT_FROZEN));
    }
    if destination.memo_required {
        return Err(Stop::Code(TOKEN_NO_MEMO));
    }
    let withheld = m.mint.fee.map_or(0, |fee| fee.withheld(m.epoch, amount));
    if withheld != 0 && !destination.fee_extension {
        return Err(Stop::Code(TOKEN_INVALID_STATE));
    }
    if m.mint.hook_set {
        // The CPI carries no hook accounts, so a hook mint never moves tokens.
        let marked = m.vault.hook_extension && destination.hook_extension;
        return Err(if marked { Stop::MissingAccount } else { Stop::InvalidAccountData });
    }
    Ok(withheld)
}

/// A malformed layout stops the load, ahead of every rule in `migrate_v2.rs`.
/// Order after those gates: the five token accounts are created (a mint under
/// the other token program or with broken extensions fails there), the gross
/// quote overflows 6024, the transfer runs, and `create_pool` takes the balance
/// increase, so it and the event carry the amount after the fee. The boost gate
/// 6027 of `migrate_v2.rs` follows. Only an account created here is closed: a
/// fee mint must be writable (6110), its withheld tokens go to the mint, and
/// any balance left fails the close with Token error 11.
pub fn migrate(m: &MigrateToken2022) -> Result<Migrated, Stop> {
    if m.mint.malformed_layout {
        return Err(Stop::InvalidAccountData);
    }
    let gated = migrate_v2::migrate_v2(&m.base);
    let (init_boost, curve_lamports) = match gated {
        Ok(Outcome::AlreadyMigrated { curve_lamports }) => return Ok(Migrated::AlreadyMigrated { curve_lamports }),
        Ok(Outcome::Migrated { init_boost, curve_lamports, .. }) => (init_boost, curve_lamports),
        Err(BaseStop::Code(OVERFLOW | NOT_ENOUGH_REMAINING_ACCOUNTS)) => (false, 0),
        Err(stop) => return Err(Stop::Base(stop)),
    };
    if !m.mint.owner_matches_program {
        return Err(Stop::IncorrectProgramId);
    }
    if m.mint.malformed_extensions {
        return Err(Stop::InvalidAccountData);
    }
    let moved = m
        .base
        .real_quote_reserves
        .checked_add(m.base.post_complete_quote_in)
        .ok_or(Stop::Code(OVERFLOW))?;
    let destination = m.pool_authority.unwrap_or(Holding {
        frozen: false,
        fee_extension: m.mint.fee.is_some(),
        memo_required: false,
        cpi_guard: false,
        non_transferable: m.mint.non_transferable,
        hook_extension: m.mint.hook_set,
    });
    let withheld = transfer(m, &destination, m.vault_balance, moved)?;
    if let Err(BaseStop::Code(code)) = gated {
        return Err(Stop::Code(code));
    }
    let closed = m.pool_authority.is_none();
    let quote = moved - withheld;
    let mut harvested = 0;
    if closed {
        if m.mint.fee.is_some() {
            if !m.mint.writable {
                return Err(Stop::Code(QUOTE_MINT_NOT_WRITABLE));
            }
            harvested = withheld;
        }
        if quote != 0 {
            return Err(Stop::Code(TOKEN_NON_NATIVE_HAS_BALANCE));
        }
    }
    Ok(Migrated::Moved(Moved {
        init_boost,
        curve_lamports,
        vault: m.vault_balance - moved,
        moved,
        withheld,
        quote,
        closed,
        pool_quote_size: created_size(&m.mint),
        harvested,
    }))
}
