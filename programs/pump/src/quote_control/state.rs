use anchor_lang::prelude::*;
use anchor_spl::token::spl_token::native_mint as spl_native_mint;
use anchor_spl::token_2022::spl_token_2022::native_mint as spl_2022_native_mint;

use crate::PumpError;

pub const QUOTE_CONTROL_SEED: &[u8] = b"quote-control";

/// Upper bound on listed quote mints; the account grows on demand up to this size.
pub const MAX_QUOTE_CONTROL_MINTS: usize = 256;

/// Admin-managed list of quote mints that may back bonding curves, each with the
/// initial virtual quote reserves used when a curve is created against it.
/// The global authority assigns `admin`; the admin assigns `reserves_admin`.
/// The account starts with room for 50 entries and is reallocated when it fills.
#[account]
#[derive(InitSpace)]
pub struct QuoteControl {
    /// May add or remove quote mints and rotate the reserves admin.
    pub admin: Pubkey,
    /// May only update the initial virtual quote reserves of listed mints.
    pub reserves_admin: Pubkey,
    pub _reserved: [u8; 32],
    #[max_len(50)]
    pub mints: Vec<QuoteControlMint>,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, InitSpace)]
pub struct QuoteControlMint {
    pub mint: Pubkey,
    pub initial_virtual_quote_reserves: u64,
}

impl QuoteControl {
    pub fn is_admin(&self, key: &Pubkey) -> bool {
        self.admin == *key
    }

    pub fn is_reserves_admin(&self, key: &Pubkey) -> bool {
        self.reserves_admin == *key
    }

    pub fn contains(&self, mint: &Pubkey) -> bool {
        self.mints.iter().position(|entry| entry.mint == *mint).is_some()
    }

    /// Serialized account size, including the discriminator, for `num_mints` entries.
    pub fn space(num_mints: usize) -> Result<usize> {
        num_mints
            .checked_mul(QuoteControlMint::INIT_SPACE)
            .and_then(|mints| mints.checked_add(8 + 32 + 32 + 32 + 4))
            .ok_or_else(|| error!(PumpError::Overflow))
    }

    /// Checks that a new quote mint may be listed.
    ///
    /// Native SOL (in either token program) and the default key are never eligible:
    /// SOL-quoted curves use the global initial virtual SOL reserves instead.
    /// The caller grows the account before appending the entry, so this only
    /// validates and never mutates the list.
    pub fn validate_new_mint(&self, mint: &Pubkey) -> Result<()> {
        require_keys_neq!(
            *mint,
            Pubkey::default(),
            PumpError::QuoteMintNotEligibleForWhitelist
        );
        require_keys_neq!(
            *mint,
            spl_native_mint::ID,
            PumpError::QuoteMintNotEligibleForWhitelist
        );
        require_keys_neq!(
            *mint,
            spl_2022_native_mint::ID,
            PumpError::QuoteMintNotEligibleForWhitelist
        );
        require_eq!(
            self.mints.iter().position(|entry| entry.mint == *mint).is_some(),
            false,
            PumpError::QuoteMintAlreadyWhitelisted
        );
        require_gt!(
            MAX_QUOTE_CONTROL_MINTS,
            self.mints.len(),
            PumpError::QuoteMintWhitelistFull
        );
        Ok(())
    }

    /// Removes a listed quote mint; existing curves keep their reserves.
    pub fn remove_mint(&mut self, mint: Pubkey) -> Result<()> {
        require_keys_neq!(
            mint,
            Pubkey::default(),
            PumpError::QuoteMintNotEligibleForWhitelist
        );
        let index = self
            .mints.iter().position(|entry| entry.mint == mint)
            .ok_or_else(|| error!(PumpError::QuoteMintNotWhitelisted))?;
        self.mints.remove(index);
        Ok(())
    }

    /// Updates the initial virtual quote reserves of a listed mint and returns the old value.
    ///
    /// Existing curves keep the virtual quote reserves they were initialized with.
    /// Callers emit the old and new values.
    pub fn set_mint_reserves(&mut self, mint: Pubkey, initial_virtual_quote_reserves: u64) -> Result<u64> {
        let index = self
            .mints
            .iter()
            .position(|entry| entry.mint == mint)
            .ok_or_else(|| error!(PumpError::QuoteMintNotWhitelisted))?;
        let entry = &mut self.mints[index];
        let old = entry.initial_virtual_quote_reserves;
        entry.initial_virtual_quote_reserves = initial_virtual_quote_reserves;
        Ok(old)
    }
}

/// Read the first matching reserve entry without constructing the account vector.
pub(crate) fn control_entry(data: &[u8], mint: &Pubkey) -> Result<Option<u64>> {
// layout-pad(22): aligns the next Source site with the original line





















    let header = data.get(..108).ok_or_else(|| error!(PumpError::InvalidQuoteControl))?;
    require!(header[..8] == *QuoteControl::DISCRIMINATOR, PumpError::InvalidQuoteControl);
    let count = u32::from_le_bytes(data[104..108].try_into().unwrap_or_default()) as usize;
// layout-pad(10): aligns the next Source site with the original line









    let entries = data.get(108..QuoteControl::space(count)?).ok_or_else(|| error!(PumpError::InvalidQuoteControl))?;
    let entry = entries.chunks_exact(QuoteControlMint::INIT_SPACE)
        .find(|entry| entry[..32] == mint.to_bytes());
    Ok(entry.map(|entry| u64::from_le_bytes(entry[32..40].try_into().unwrap_or_default())))
}
