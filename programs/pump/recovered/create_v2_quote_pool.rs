//! The pool record of Pump `create_v2`: pricing a coin quoted by a migrated
//! curve from that curve's PumpSwap pool, which `create_v2.rs` leaves out. A
//! quote curve with all four reserves at zero is priced from
//! `[curve, pool, base vault, quote vault]` in the remaining accounts.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_create_v2_quote_pool_captured.py`.
//!
//! Unconfirmed (미확인, outside the checked inputs): a pool record that is not
//! the root of the quote chain, vaults holding Token-2022 extensions other than
//! the account-type byte, and the arithmetic overflow paths named below.

pub const OVERFLOW: u32 = 6024;
pub const DIVISION_BY_ZERO: u32 = 6026;
pub const QUOTE_POOL_ACCOUNTS_REQUIRED: u32 = 6101;
pub const QUOTE_POOL_NOT_FOUND: u32 = 6102;
pub const INVALID_QUOTE_POOL: u32 = 6103;
pub const QUOTE_RESERVES_OUT_OF_RANGE: u32 = 6104;

/// The pool's vault as `vault_amount` reads it.
pub struct Vault {
    /// Owned by SPL Token or Token-2022.
    pub owner_ok: bool,
    pub len: usize,
    /// Byte 108, the token account state.
    pub state: u8,
    /// Byte 165, the account type of an extended account.
    pub account_type: u8,
    pub amount: u64,
}

pub struct Pool {
    /// Remaining accounts from the quote curve on.
    pub tail: usize,
    /// The canonical pool PDA of the curve's pool authority and mints.
    pub key_ok: bool,
    /// Owned by PumpSwap.
    pub owner_ok: bool,
    pub len: usize,
    pub discriminator_ok: bool,
    /// The accounts passed are the vaults the pool stores at 139 and 171.
    pub base_key_ok: bool,
    pub quote_key_ok: bool,
    pub base: Vault,
    pub quote: Vault,
    /// Stored at 245, read only from accounts of 261 bytes or more.
    pub adjustment: i128,
}

/// The `Global` reserves and the seed of the quote chain's root.
pub struct Seed {
    pub initial_virtual_token_reserves: u64,
    pub initial_real_token_reserves: u64,
    pub seed: u64,
}

/// `vault_amount`: only 165 bytes, or more than that with account type 2. 355
/// bytes is refused outright, before the state byte.
fn vault_amount(v: &Vault) -> Result<u64, u32> {
    if !v.owner_ok || v.len < 165 || v.len == 355 || v.state != 1 {
        return Err(INVALID_QUOTE_POOL);
    }
    if v.len != 165 && v.account_type != 2 {
        return Err(INVALID_QUOTE_POOL);
    }
    Ok(v.amount)
}

/// Pool reserves, in the checks' order. Both vaults are read only after the pool
/// names them; which goes first is 미확인, their failures share a code.
fn pool_record(p: &Pool) -> Result<(u64, u128), u32> {
    if p.tail < 4 {
        return Err(QUOTE_POOL_ACCOUNTS_REQUIRED);
    }
    if !p.key_ok {
        return Err(INVALID_QUOTE_POOL);
    }
    if !p.owner_ok {
        return Err(QUOTE_POOL_NOT_FOUND);
    }
    if p.len < 211 || !p.discriminator_ok || !p.base_key_ok || !p.quote_key_ok {
        return Err(INVALID_QUOTE_POOL);
    }
    let base = vault_amount(&p.base)?;
    let quote = vault_amount(&p.quote)?;
    let adjustment = if p.len >= 261 { p.adjustment } else { 0 };
    let quote = (quote as i128).checked_add(adjustment).and_then(|v| u128::try_from(v).ok()).ok_or(OVERFLOW)?;
    Ok((base, quote))
}

/// The new curve's virtual quote reserves: the seed's initial buy goes through
/// the pool's constant product and is scaled back.
/// The overflow checks on the sum, the products, and the `u64` result are 미확인:
/// carried over from the program sources, no captured case enters them.
pub fn reserves(p: &Pool, s: &Seed) -> Result<u64, u32> {
    let (base, quote) = pool_record(p)?;
    let real = s.initial_real_token_reserves as u128;
    let difference = (s.initial_virtual_token_reserves as u128).checked_sub(real).ok_or(OVERFLOW)?;
    let amount = (real * s.seed as u128).checked_div(difference).ok_or(DIVISION_BY_ZERO)?;
    if quote == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    let denominator = quote.checked_add(amount).ok_or(OVERFLOW)?;
    let numerator = (base as u128).checked_mul(amount).ok_or(OVERFLOW)?;
    let output = numerator / denominator;
    let scaled = output.checked_mul(difference).ok_or(OVERFLOW)?.checked_div(real).ok_or(DIVISION_BY_ZERO)?;
    let reserves = u64::try_from(scaled).map_err(|_| OVERFLOW)?;
    if reserves == 0 {
        return Err(QUOTE_RESERVES_OUT_OF_RANGE);
    }
    Ok(reserves)
}
