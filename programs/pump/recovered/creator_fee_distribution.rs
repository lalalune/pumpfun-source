//! Captured behavior of Pump `distribute_creator_fees` (native creator vaults
//! owned by a pump_fees SharingConfig) and the read-only
//! `get_minimum_distributable_fee` query that shares its arithmetic.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_creator_fee_distribution_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.
//!
//! Observed facts worth knowing:
//! - Distribution is all-or-nothing on a minimum: every shareholder short of
//!   its rent minimum sets a threshold `ceil(deficit * 10000 / bps)` on the
//!   distributable lamports. Below the largest threshold the instruction
//!   succeeds, moves nothing and emits no event (return data still carries
//!   `distributed = 0`).
//! - Shares are not re-validated here. A config whose bps sum exceeds 10000
//!   pays more than the vault's distributable lamports (eating into the
//!   vault's rent reserve), and fails with System error 1 only once the vault
//!   cannot cover a transfer.
//! - `get_minimum_distributable_fee` ignores the config status, an unswept
//!   `creator_fee` and the curve's quote mint, so it can report
//!   `can_distribute = true` for a distribution that fails.

pub const MINT_DOES_NOT_MATCH_BONDING_CURVE: u32 = 6004;
pub const OVERFLOW: u32 = 6024;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: u32 = 6027;
pub const SHARING_CONFIG_NOT_ACTIVE: u32 = 6051;
pub const EXECUTABLE_RECIPIENT: u32 = 6052;
pub const CREATOR_MISMATCH: u32 = 6053;
pub const SHAREHOLDER_MISMATCH: u32 = 6054;
pub const INVALID_SHARE_BPS: u32 = 6055;
pub const UNSUPPORTED_QUOTE_MINT: u32 = 6063;
pub const CREATOR_FEES_NOT_SWEPT: u32 = 6095;
/// System program `ResultWithNegativeLamports`.
pub const SYSTEM_INSUFFICIENT_LAMPORTS: u32 = 1;

pub fn rent_minimum(data_len: u64) -> u64 {
    (128 + data_len) * 6960
}

/// The account passed in a shareholder's remaining-account slot.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Slot {
    /// The configured address, a system account with this balance and size.
    Holder { lamports: u64, data_len: u64 },
    /// Some other address.
    Wrong,
    /// The configured address is an executable program.
    Executable,
}

pub struct Shareholder {
    pub bps: u16,
    /// `None`: no remaining account in this position.
    pub slot: Option<Slot>,
}

pub struct Distribution {
    pub vault_lamports: u64,
    pub shareholders: Vec<Shareholder>,
    pub active: bool,
    pub creator_fee: u64,
    pub curve_creator_is_config: bool,
    pub curve_has_quote_mint: bool,
    pub config_mint_matches: bool,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Amounts {
    pub transfers: Vec<u64>,
    pub minimum_distributable: u64,
    pub minimum_vault_balance: u64,
    pub available: u64,
}

pub fn amounts(d: &Distribution) -> Result<Amounts, u32> {
    let reserve = rent_minimum(0);
    let available = d.vault_lamports.saturating_sub(reserve);
    let mut transfers = Vec::new();
    let mut minimum = 0u64;
    for share in &d.shareholders {
        let (lamports, data_len) = match share.slot.ok_or(NOT_ENOUGH_REMAINING_ACCOUNTS)? {
            Slot::Wrong => return Err(SHAREHOLDER_MISMATCH),
            Slot::Executable => return Err(EXECUTABLE_RECIPIENT),
            Slot::Holder { lamports, data_len } => (lamports, data_len),
        };
        if share.bps == 0 {
            return Err(INVALID_SHARE_BPS);
        }
        let bps = u64::from(share.bps);
        let deficit = rent_minimum(data_len).saturating_sub(lamports);
        let threshold = deficit
            .checked_mul(10_000)
            .and_then(|v| v.checked_add(bps - 1))
            .ok_or(OVERFLOW)?
            / bps;
        minimum = minimum.max(threshold);
        transfers.push(available.checked_mul(bps).ok_or(OVERFLOW)? / 10_000);
    }
    Ok(Amounts { transfers, minimum_distributable: minimum, minimum_vault_balance: minimum.saturating_add(reserve), available })
}

fn check_accounts(d: &Distribution, distribute: bool) -> Result<(), u32> {
    if distribute && d.curve_has_quote_mint {
        return Err(UNSUPPORTED_QUOTE_MINT);
    }
    if !d.curve_creator_is_config {
        return Err(CREATOR_MISMATCH);
    }
    if !d.config_mint_matches {
        return Err(MINT_DOES_NOT_MATCH_BONDING_CURVE);
    }
    Ok(())
}

#[derive(Debug, PartialEq, Eq)]
pub struct Distributed {
    /// Lamports sent to each shareholder (all zero when below the minimum).
    pub transfers: Vec<u64>,
    pub distributed: u64,
    /// Whether DistributeCreatorFeesEvent is emitted.
    pub event: bool,
}

pub fn distribute(d: &Distribution) -> Result<Distributed, u32> {
    check_accounts(d, true)?;
    if !d.active {
        return Err(SHARING_CONFIG_NOT_ACTIVE);
    }
    if d.creator_fee != 0 {
        return Err(CREATOR_FEES_NOT_SWEPT);
    }
    let a = amounts(d)?;
    if a.available < a.minimum_distributable {
        return Ok(Distributed { transfers: vec![0; a.transfers.len()], distributed: 0, event: false });
    }
    let mut vault = d.vault_lamports;
    let mut distributed = 0u64;
    for &amount in &a.transfers {
        vault = vault.checked_sub(amount).ok_or(SYSTEM_INSUFFICIENT_LAMPORTS)?;
        distributed = distributed.checked_add(amount).ok_or(OVERFLOW)?;
    }
    Ok(Distributed { transfers: a.transfers, distributed, event: true })
}

#[derive(Debug, PartialEq, Eq)]
pub struct Minimum {
    pub minimum_required: u64,
    pub distributable_fees: u64,
    pub can_distribute: bool,
}

pub fn minimum(d: &Distribution) -> Result<Minimum, u32> {
    check_accounts(d, false)?;
    let a = amounts(d)?;
    Ok(Minimum {
        minimum_required: a.minimum_vault_balance,
        distributable_fees: a.available,
        can_distribute: a.available >= a.minimum_distributable,
    })
}
