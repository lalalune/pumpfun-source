//! Pure model of Pump `distribute_creator_fees_v2` on its SPL-quote path (a
//! bonding curve whose `quote_mint` is set), as observed on the captured
//! program (`evidence/original/pump/deployed.so`).
//!
//! Observed rules, checked by
//! `tests/test_creator_fee_distribution_quote_captured.py`:
//! * Account checks: curve creator must be the sharing config (6053), the
//!   config's mint must match (6004), and the passed quote mint must be the
//!   curve's quote mint (6004). Then status must be Active (6051) and the
//!   curve's `creator_fee` must be swept (6095). A missing vault quote token
//!   account fails with InvalidAccountData.
//! * Remaining accounts are all shareholder wallets first, then all their
//!   associated token accounts. Per shareholder, in order: wallet slot (6027),
//!   ATA slot (6027), wallet key (6054), ATA address (6054), executable
//!   wallet (6052), zero bps (6055), `vault_tokens * bps` overflow (6024),
//!   and a missing ATA without `initialize_ata` (6070).
//! * Each share is `vault_tokens * bps / 10000`, floored, with no rent
//!   minimum: a zero-token share still transfers 0 and, with
//!   `initialize_ata`, the payer still funds that shareholder's ATA
//!   (2,039,280 lamports each).
//! * Shares above 10,000 bps are not rejected; the token transfer that runs
//!   past the vault balance fails in the token program (custom error 1).
//! * On success the event and return data carry `distributed` and the quote
//!   mint; the native creator vault lamports are not touched.
//!
//! This is a behavioural model of matching outcomes on synthetic inputs, not a
//! byte-identity or source-recovery claim.

pub const MINT_MISMATCH: u32 = 6004;
pub const OVERFLOW: u32 = 6024;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: u32 = 6027;
pub const SHARING_CONFIG_NOT_ACTIVE: u32 = 6051;
pub const EXECUTABLE_RECIPIENT: u32 = 6052;
pub const CREATOR_MISMATCH: u32 = 6053;
pub const SHAREHOLDER_MISMATCH: u32 = 6054;
pub const INVALID_SHARE_BPS: u32 = 6055;
pub const UNINITIALIZED_ATA: u32 = 6070;
pub const CREATOR_FEES_NOT_SWEPT: u32 = 6095;
pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;
pub const TOKEN_ACCOUNT_RENT: u64 = 2_039_280;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Wallet {
    Ok,
    Wrong,
    Executable,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Ata {
    Exists,
    Absent,
    Wrong,
}

#[derive(Clone, Copy, Debug)]
pub struct Shareholder {
    pub bps: u16,
    /// None when the remaining accounts stop before this wallet slot.
    pub wallet: Option<Wallet>,
    /// None when the remaining accounts stop before this ATA slot.
    pub ata: Option<Ata>,
}

#[derive(Clone, Debug)]
pub struct QuoteDistribution {
    pub vault_tokens: Option<u64>,
    pub shareholders: Vec<Shareholder>,
    pub active: bool,
    pub creator_fee: u64,
    pub curve_creator_is_config: bool,
    pub config_mint_matches: bool,
    pub quote_mint_matches: bool,
    pub initialize_ata: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Failure {
    Custom(u32),
    InvalidAccountData,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Distributed {
    pub transfers: Vec<u64>,
    pub distributed: u64,
    /// ATAs created at the payer's expense.
    pub created_atas: usize,
}

impl Distributed {
    /// Lamports the payer spends on new shareholder token accounts.
    pub fn payer_ata_rent(&self) -> u64 {
        self.created_atas as u64 * TOKEN_ACCOUNT_RENT
    }
}

pub fn distribute(d: &QuoteDistribution) -> Result<Distributed, Failure> {
    if !d.curve_creator_is_config {
        return Err(Failure::Custom(CREATOR_MISMATCH));
    }
    if !d.config_mint_matches || !d.quote_mint_matches {
        return Err(Failure::Custom(MINT_MISMATCH));
    }
    if !d.active {
        return Err(Failure::Custom(SHARING_CONFIG_NOT_ACTIVE));
    }
    if d.creator_fee != 0 {
        return Err(Failure::Custom(CREATOR_FEES_NOT_SWEPT));
    }
    let source = d.vault_tokens.ok_or(Failure::InvalidAccountData)?;
    let mut plan = Vec::with_capacity(d.shareholders.len());
    for share in &d.shareholders {
        let wallet = share.wallet.ok_or(Failure::Custom(NOT_ENOUGH_REMAINING_ACCOUNTS))?;
        let ata = share.ata.ok_or(Failure::Custom(NOT_ENOUGH_REMAINING_ACCOUNTS))?;
        if wallet == Wallet::Wrong || ata == Ata::Wrong {
            return Err(Failure::Custom(SHAREHOLDER_MISMATCH));
        }
        if wallet == Wallet::Executable {
            return Err(Failure::Custom(EXECUTABLE_RECIPIENT));
        }
        if share.bps == 0 {
            return Err(Failure::Custom(INVALID_SHARE_BPS));
        }
        let amount = source.checked_mul(u64::from(share.bps)).ok_or(Failure::Custom(OVERFLOW))? / 10_000;
        let needs_initialize = ata == Ata::Absent;
        if needs_initialize && !d.initialize_ata {
            return Err(Failure::Custom(UNINITIALIZED_ATA));
        }
        plan.push((amount, needs_initialize));
    }
    let mut remaining = source;
    let mut distributed = 0u64;
    let mut created_atas = 0;
    for (amount, needs_initialize) in &plan {
        created_atas += usize::from(*needs_initialize);
        remaining = remaining.checked_sub(*amount).ok_or(Failure::Custom(TOKEN_INSUFFICIENT_FUNDS))?;
        distributed = distributed.checked_add(*amount).ok_or(Failure::Custom(OVERFLOW))?;
    }
    Ok(Distributed { transfers: plan.iter().map(|p| p.0).collect(), distributed, created_atas })
}
