//! `set_mayhem_virtual_params`: Mayhem's resync of a bonding curve's virtual
//! quote reserve against the Mayhem sol-vault token balance.
//!
//! A pure model of which account check stops the call, whether
//! `virtual_quote_reserves` is rewritten and to what, and the six reserve
//! fields of `UpdateMayhemVirtualParamsEvent` (the event is emitted on every
//! successful call, including the ones that change nothing). Checked against
//! the captured Pump, Token-2022 and Associated Token programs by
//! `tests/test_mayhem_virtual_params_captured.py`, which signs the Mayhem
//! `["sol-vault"]` PDA through `scripts/fixtures/signer_stub.so`; that is
//! matching behaviour on the inputs listed there, not a byte-identity claim.

/// Cap on the new virtual quote reserve for SOL-quoted curves.
pub const NATIVE_CAP: u64 = 2_000_000_000_000;
/// Cap on the new virtual quote reserve for SPL-quoted curves.
pub const QUOTE_CAP: u64 = 160_000_000_000;
/// Smallest real quote reserve that triggers a resync (SOL quote).
pub const NATIVE_MIN_REAL_QUOTE: u64 = 10_000_000;
/// Smallest real quote reserve that triggers a resync (SPL quote).
pub const QUOTE_MIN_REAL_QUOTE: u64 = 1_000_000;
/// Smallest denominator that triggers a resync.
pub const MIN_DENOMINATOR: u64 = 1_000_000_000_000;

/// Anchor and runtime error numbers.
pub const ACCOUNT_DID_NOT_DESERIALIZE: u32 = 3003;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const CONSTRAINT_SIGNER: u32 = 2002;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const CONSTRAINT_ASSOCIATED: u32 = 2009;
pub const CONSTRAINT_TOKEN_OWNER: u32 = 2015;
pub const CONSTRAINT_ASSOCIATED_TOKEN_PROGRAM: u32 = 2023;
pub const INVALID_NUMERIC_CONVERSION: u32 = 4102;
pub const OVERFLOW: u32 = 6024;

/// Which account inputs are well formed. `false` breaks exactly that check.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Accounts {
    /// `global` deserializes as `Global`.
    pub global_ok: bool,
    /// `token_program` is Token-2022.
    pub token_program_ok: bool,
    /// `sol_vault_authority` signed (only a Mayhem CPI can sign it).
    pub signed: bool,
    /// `sol_vault_authority` is Mayhem's `["sol-vault"]` PDA.
    pub seeds_ok: bool,
    /// `mayhem_token_vault` is owned by `token_program`.
    pub vault_program_ok: bool,
    /// `mayhem_token_vault`'s token owner is `sol_vault_authority`.
    pub vault_owner_ok: bool,
    /// `mayhem_token_vault` is the canonical ATA of (sol vault, mint).
    pub vault_address_ok: bool,
    /// `bonding_curve` is the `["bonding-curve", mint]` PDA.
    pub curve_ok: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Curve {
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub token_total_supply: u64,
    pub complete: bool,
    pub is_mayhem_mode: bool,
    /// `quote_mint` is the default key (SOL quote).
    pub native_quote: bool,
}

/// The reserve fields of `UpdateMayhemVirtualParamsEvent` (timestamp and mint
/// are the clock and the mint key).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Event {
    pub virtual_token_reserves: u64,
    pub virtual_sol_reserves: u64,
    pub new_virtual_token_reserves: u64,
    pub new_virtual_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub real_sol_reserves: u64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Outcome {
    Error(u32),
    Synced(Event),
}

/// First failing account check. Typed accounts are loaded in declaration
/// order before any constraint runs, so `global` and `token_program` fail
/// first; then the constraints of `sol_vault_authority` (seeds before the
/// signer flag), the vault (token
/// program, then token owner, then ATA address) and the curve seeds.
pub fn check_accounts(a: &Accounts) -> Option<u32> {
    if !a.global_ok {
        return Some(ACCOUNT_DID_NOT_DESERIALIZE);
    }
    if !a.token_program_ok {
        return Some(INVALID_PROGRAM_ID);
    }
    if !a.seeds_ok {
        return Some(CONSTRAINT_SEEDS);
    }
    if !a.signed {
        return Some(CONSTRAINT_SIGNER);
    }
    if !a.vault_program_ok {
        return Some(CONSTRAINT_ASSOCIATED_TOKEN_PROGRAM);
    }
    if !a.vault_owner_ok {
        return Some(CONSTRAINT_TOKEN_OWNER);
    }
    if !a.vault_address_ok {
        return Some(CONSTRAINT_ASSOCIATED);
    }
    if !a.curve_ok {
        return Some(CONSTRAINT_SEEDS);
    }
    None
}

/// New `virtual_quote_reserves`, or the error. Complete and non-Mayhem
/// curves are left alone. The denominator is computed (and can overflow)
/// before the thresholds are looked at; the quotient is narrowed to u64
/// before it is capped.
pub fn sync(c: &Curve, initial_real_token_reserves: u64, vault_amount: u64) -> Result<u64, u32> {
    if c.complete || !c.is_mayhem_mode {
        return Ok(c.virtual_quote_reserves);
    }
    let denominator = c
        .token_total_supply
        .checked_mul(2)
        .and_then(|v| v.checked_sub(initial_real_token_reserves))
        .and_then(|v| v.checked_sub(vault_amount))
        .ok_or(OVERFLOW)?;
    let min_real = if c.native_quote { NATIVE_MIN_REAL_QUOTE } else { QUOTE_MIN_REAL_QUOTE };
    if c.real_quote_reserves < min_real || denominator < MIN_DENOMINATOR {
        return Ok(c.virtual_quote_reserves);
    }
    let numerator = (denominator as u128 + c.virtual_token_reserves as u128)
        .checked_mul(c.real_quote_reserves as u128)
        .ok_or(OVERFLOW)?;
    let computed = u64::try_from(numerator / denominator as u128).map_err(|_| INVALID_NUMERIC_CONVERSION)?;
    Ok(computed.min(if c.native_quote { NATIVE_CAP } else { QUOTE_CAP }))
}

pub fn set_mayhem_virtual_params(a: &Accounts, c: &Curve, initial_real_token_reserves: u64, vault_amount: u64) -> Outcome {
    if let Some(code) = check_accounts(a) {
        return Outcome::Error(code);
    }
    match sync(c, initial_real_token_reserves, vault_amount) {
        Err(code) => Outcome::Error(code),
        Ok(new_quote) => Outcome::Synced(Event {
            virtual_token_reserves: c.virtual_token_reserves,
            virtual_sol_reserves: c.virtual_quote_reserves,
            new_virtual_token_reserves: c.virtual_token_reserves,
            new_virtual_sol_reserves: new_quote,
            real_token_reserves: c.real_token_reserves,
            real_sol_reserves: c.real_quote_reserves,
        }),
    }
}
