//! Captured end-to-end outcome of Pump `migrate_v2` with the real pump_amm
//! program, on native, SPL and Token-2022 quote curves: the pool `create_pool`
//! builds, who pays each rent, what the boost moves, and what
//! `withdraw_authority` and `user` end with once the temporary accounts close.
//!
//! `migrate_v2.rs` stops at the arguments of the CPI because its test replaces
//! pump_amm with a no-op. This module carries on from there. Checked against
//! `evidence/original/pump/deployed.so`, `evidence/original/pump_amm/deployed.so`
//! and the captured token programs by `tests/test_migrate_v2_pool_captured.py`.
//! Not linked into the SBF crate. This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): the account faults, which
//! `migrate_v2.rs` holds; a curve or user short of funds on the token routes;
//! frozen accounts; Token-2022 extensions other than the transfer fee; and the
//! order among rent failures, which all share one code.

/// System program `ResultWithNegativeLamports`: the rent payer ran out.
pub const INSUFFICIENT_LAMPORTS: i64 = 1;
/// System program `AccountAlreadyInUse`: pool or LP mint already exists.
pub const ACCOUNT_IN_USE: i64 = 0;
/// Associated Token `Create` (not idempotent) on an account that exists: the
/// runtime's `IllegalOwner`, not a custom code.
pub const ILLEGAL_OWNER: i64 = -1;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: i64 = 6027;
pub const OVERFLOW: i64 = 6024;
/// pump_amm codes.
pub const AMM_UNSUPPORTED_BASE_MINT: i64 = 6006;
pub const AMM_ZERO_BASE: i64 = 6001;
pub const AMM_ZERO_QUOTE: i64 = 6002;
pub const AMM_TOO_LITTLE_LIQUIDITY: i64 = 6003;
pub const AMM_DISABLED_CREATE_POOL: i64 = 6017;
pub const AMM_TRUNCATION: i64 = 6024;
pub const AMM_MAYHEM_DISABLED: i64 = 6041;
pub const AMM_CASHBACK_NOT_ENABLED: i64 = 6049;

pub const TOKEN_ACCOUNT_RENT: u64 = 2_039_280;
/// A Token-2022 account with the immutable-owner extension.
pub const TOKEN_2022_ACCOUNT_RENT: u64 = 2_074_080;
pub const LP_ACCOUNT_RENT: u64 = TOKEN_2022_ACCOUNT_RENT;
/// The same with the transfer fee amount extension.
pub const TOKEN_2022_FEE_ACCOUNT_RENT: u64 = 2_157_600;
pub const LP_MINT_RENT: u64 = 1_461_600;
pub const POOL_RENT: u64 = 2_888_400;
pub const MINIMUM_LIQUIDITY: u64 = 100;
pub const BOOST_DENOMINATOR: u128 = 1_000_000_000_000_000;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Quote {
    /// `bonding_curve.quote_mint` unset: WSOL funded from the curve's lamports.
    Native,
    Spl,
    Token2022 { fee_bps: u16 },
}

pub struct Migration {
    pub quote_route: Quote,
    pub curve_tokens: u64,
    pub real_quote_reserves: u64,
    pub post_complete_quote_in: u64,
    pub pool_migration_fee: u64,
    pub curve_mayhem: bool,
    pub curve_cashback: bool,
    /// Balances of accounts that exist before the call (`None`: created here).
    pub authority_mint_account: Option<u64>,
    pub authority_quote_account: Option<u64>,
    pub pool_base_account: Option<u64>,
    pub pool_quote_account: Option<u64>,
    pub user_lp_account: bool,
    /// Lamports already on system-owned accounts.
    pub authority_lamports: u64,
    pub pool_lamports: u64,
    pub lp_mint_lamports: u64,
    /// `pool` or `lp_mint` already initialized.
    pub pool_taken: bool,
    pub lp_mint_taken: bool,
    pub disable_create: bool,
    pub mayhem_enabled: bool,
    pub cashback_enabled: bool,
    pub boost_enabled: bool,
    pub remaining_accounts: usize,
    pub boost_vault_exists: bool,
    pub token_2022_base: bool,
    /// Transfer fee of a Token-2022 base mint, in basis points (no ceiling here).
    pub transfer_fee_bps: u16,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Migrated {
    pub base: u64,
    /// What reached the pool authority's account: the migration event's amount.
    pub quote: u64,
    pub initial_liquidity: u64,
    pub lp_out: u64,
    pub pool_base_after: u64,
    pub pool_quote_after: u64,
    /// Quote that entered the boost vault's transfer; the virtual reserves.
    pub boosted: u64,
    pub vault_after: u64,
    pub user_paid: u64,
    pub withdraw_gain: u64,
    pub quote_left: Option<u64>,
}

fn pay(lamports: &mut u64, amount: u64) -> Result<(), i64> {
    *lamports = lamports.checked_sub(amount).ok_or(INSUFFICIENT_LAMPORTS)?;
    Ok(())
}

fn isqrt(value: u128) -> u64 {
    let (mut low, mut high) = (0u128, 1u128 << 64);
    while high - low > 1 {
        let middle = (low + high) / 2;
        if middle * middle <= value {
            low = middle;
        } else {
            high = middle;
        }
    }
    low as u64
}

fn after_fee(amount: u64, bps: u16) -> u64 {
    amount - (amount as u128 * bps as u128).div_ceil(10_000) as u64
}

pub fn migrate(m: &Migration) -> Result<Migrated, i64> {
    let native = m.quote_route == Quote::Native;
    let quote_fee = match m.quote_route {
        Quote::Token2022 { fee_bps } => fee_bps,
        _ => 0,
    };
    let quote_rent = match m.quote_route {
        Quote::Token2022 { fee_bps: 0 } => TOKEN_2022_ACCOUNT_RENT,
        Quote::Token2022 { .. } => TOKEN_2022_FEE_ACCOUNT_RENT,
        _ => TOKEN_ACCOUNT_RENT,
    };
    let base_rent = if m.token_2022_base { TOKEN_2022_ACCOUNT_RENT } else { TOKEN_ACCOUNT_RENT };
    let mut authority = m.authority_lamports + m.pool_migration_fee;
    // On token routes `user` pays the fee and the four accounts; the fee only
    // pays pump_amm's rents.
    let mut user_paid = if native { 0 } else { m.pool_migration_fee };
    for (account, rent) in [
        (m.pool_base_account, base_rent),
        (m.pool_quote_account, quote_rent),
        (m.authority_mint_account, base_rent),
        (m.authority_quote_account, quote_rent),
    ] {
        if account.is_none() {
            if native {
                pay(&mut authority, rent)?;
            } else {
                user_paid += rent;
            }
        }
    }
    let base = m.authority_mint_account.unwrap_or(0) + after_fee(m.curve_tokens, m.transfer_fee_bps);
    let reserves = m.real_quote_reserves.checked_add(m.post_complete_quote_in).ok_or(OVERFLOW)?;
    let quote = if native { reserves.checked_sub(m.pool_migration_fee).ok_or(OVERFLOW)? } else { after_fee(reserves, quote_fee) };
    // pump_amm's `init` constraints run before any of its handler checks.
    if m.pool_taken {
        return Err(ACCOUNT_IN_USE);
    }
    pay(&mut authority, POOL_RENT.saturating_sub(m.pool_lamports))?;
    if m.lp_mint_taken {
        return Err(ACCOUNT_IN_USE);
    }
    pay(&mut authority, LP_MINT_RENT.saturating_sub(m.lp_mint_lamports))?;
    if m.user_lp_account {
        return Err(ILLEGAL_OWNER);
    }
    pay(&mut authority, LP_ACCOUNT_RENT)?;
    if m.curve_mayhem && !m.mayhem_enabled {
        return Err(AMM_MAYHEM_DISABLED);
    }
    if m.curve_cashback && !m.cashback_enabled {
        return Err(AMM_CASHBACK_NOT_ENABLED);
    }
    if m.disable_create {
        return Err(AMM_DISABLED_CREATE_POOL);
    }
    if base == 0 {
        return Err(AMM_ZERO_BASE);
    }
    if quote == 0 {
        return Err(AMM_ZERO_QUOTE);
    }
    if m.transfer_fee_bps != 0 {
        return Err(AMM_UNSUPPORTED_BASE_MINT);
    }
    // Sized on what the pool's accounts hold after the deposit, not on the deposit.
    let pool_base_after = m.pool_base_account.unwrap_or(0) + base;
    // A quote transfer fee is charged again on the way into the pool.
    let mut pool_quote_after = m.pool_quote_account.unwrap_or(0) + after_fee(quote, quote_fee);
    let initial_liquidity = isqrt(pool_base_after as u128 * pool_quote_after as u128);
    if initial_liquidity < MINIMUM_LIQUIDITY {
        return Err(AMM_TOO_LITTLE_LIQUIDITY);
    }
    let (mut boosted, mut vault_after) = (0, 0);
    if !m.curve_mayhem {
        if m.remaining_accounts == 2 {
            // The rent comes from `user`, and goes back to `user` if unspent.
            if !m.boost_vault_exists {
                user_paid += quote_rent;
            }
            if m.boost_enabled {
                let amount = pool_base_after as u128 * pool_quote_after as u128 / BOOST_DENOMINATOR;
                let amount = u64::try_from(amount).map_err(|_| AMM_TRUNCATION)?;
                if amount != 0 && amount < pool_quote_after {
                    boosted = amount;
                    pool_quote_after -= amount;
                    vault_after = after_fee(amount, quote_fee);
                }
            }
        } else if m.boost_enabled {
            return Err(NOT_ENOUGH_REMAINING_ACCOUNTS);
        }
    }
    // Closing refunds each temporary account's rent. A quote account Pump did
    // not create stays open and keeps its old balance.
    authority += LP_ACCOUNT_RENT + if m.authority_mint_account.is_none() { base_rent } else { TOKEN_ACCOUNT_RENT };
    if m.authority_quote_account.is_none() {
        authority += quote_rent;
    }
    Ok(Migrated {
        base,
        quote,
        initial_liquidity,
        lp_out: initial_liquidity - MINIMUM_LIQUIDITY,
        pool_base_after,
        pool_quote_after,
        boosted,
        vault_after,
        user_paid,
        withdraw_gain: authority,
        quote_left: m.authority_quote_account,
    })
}
