//! Pure model of Pump `collect_creator_fee` and `collect_creator_fee_v2`
//! as observed on the captured program (`evidence/original/pump/deployed.so`).
//!
//! Observed rules, checked by `tests/test_creator_fee_collect_captured.py`:
//! * Nobody has to sign for the creator: any payer can push the vault to the
//!   creator account bound by the `creator-vault` seeds.
//! * A creator account owned by the Pump Fees program fails with 6050
//!   (`UnableToDistributeCreatorVaultMigratedToSharingConfig`) before any
//!   other check, including on the SPL path and with an empty vault.
//! * An executable creator returns Ok with no transfer and no event, on every
//!   path (SPL tokens stay in the vault's token account too).
//! * Native path (v1, and v2 with the WSOL mint): amount = vault lamports minus
//!   the zero-byte rent (890,880), saturating. 0 returns Ok with no event. If
//!   the creator's lamports plus amount stay below rent for the creator's
//!   data length, it returns Ok with no transfer and no event. A credit that
//!   overflows u64 fails in the System program with ArithmeticOverflow.
//!   The event's `quote_mint` is the default key even for v2 with WSOL.
//! * SPL path (v2, other mints): the whole token balance of the vault's ATA is
//!   moved to the creator's ATA; vault lamports and creator rent are ignored.
//!   A missing vault ATA fails with InvalidAccountData; a zero balance returns
//!   Ok with no event; a missing creator ATA fails in the token program with
//!   InvalidAccountData.
//!
//! This is a behavioural model of matching outcomes on synthetic inputs, not a
//! byte-identity or source-recovery claim.

pub const MIGRATED_TO_SHARING_CONFIG: u32 = 6050;
pub const ZERO_BYTE_RENT: u64 = 890_880;

pub fn rent_minimum(data_len: u64) -> u64 {
    (128 + data_len) * 6_960
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Quote {
    /// `collect_creator_fee`, or `collect_creator_fee_v2` with the WSOL mint.
    Native,
    /// `collect_creator_fee_v2` with any other mint.
    Spl { vault_tokens: Option<u64>, creator_ata_exists: bool },
}

#[derive(Clone, Copy, Debug)]
pub struct Collect {
    pub creator_owned_by_fees: bool,
    pub creator_executable: bool,
    pub creator_lamports: u64,
    pub creator_data_len: u64,
    pub vault_lamports: u64,
    pub quote: Quote,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CollectError {
    Custom(u32),
    InvalidAccountData,
    ArithmeticOverflow,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub struct Collected {
    /// Lamports moved from the creator vault to the creator.
    pub lamports: u64,
    /// Tokens moved from the vault ATA to the creator ATA.
    pub tokens: u64,
    /// Whether CollectCreatorFeeEvent is emitted.
    pub event: bool,
}

pub fn collect(c: &Collect) -> Result<Collected, CollectError> {
    if c.creator_owned_by_fees {
        return Err(CollectError::Custom(MIGRATED_TO_SHARING_CONFIG));
    }
    if c.creator_executable {
        return Ok(Collected::default());
    }
    match c.quote {
        Quote::Native => {
            let amount = c.vault_lamports.saturating_sub(ZERO_BYTE_RENT);
            if amount == 0 {
                return Ok(Collected::default());
            }
            if c.creator_lamports.saturating_add(amount) < rent_minimum(c.creator_data_len) {
                return Ok(Collected::default());
            }
            c.creator_lamports.checked_add(amount).ok_or(CollectError::ArithmeticOverflow)?;
            Ok(Collected { lamports: amount, tokens: 0, event: true })
        }
        Quote::Spl { vault_tokens, creator_ata_exists } => {
            let amount = vault_tokens.ok_or(CollectError::InvalidAccountData)?;
            if amount == 0 {
                return Ok(Collected::default());
            }
            if !creator_ata_exists {
                return Err(CollectError::InvalidAccountData);
            }
            Ok(Collected { lamports: 0, tokens: amount, event: true })
        }
    }
}
