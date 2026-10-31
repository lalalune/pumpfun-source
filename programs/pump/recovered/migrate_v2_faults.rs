//! Captured faults of Pump `migrate_v2` with the real pump_amm program: which
//! Token-2022 mint extensions pump_amm admits on each side of the new pool, what
//! an extension changes in the rent `user` pays, frozen token accounts, a wrapped
//! SOL quote curve, and a `user` or curve account short of funds.
//!
//! `tests/test_migrate_v2_captured.py` replaces pump_amm with a no-op, so none of
//! this runs there. Checked against `evidence/original/pump/deployed.so`,
//! `evidence/original/pump_amm/deployed.so` and the captured token programs by
//! `tests/test_migrate_v2_faults_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): non-zero transfer fee rates;
//! extension bodies other than the ones the test writes; a transfer hook program
//! that really runs; a base mint with both extensions 10 and 16, which fails with
//! `InvalidAccountData` for a reason not pinned here.

/// `ResultWithNegativeLamports` from the System program, and SPL `InsufficientFunds`.
pub const INSUFFICIENT: i64 = 1;
/// System program `AccountAlreadyInUse`.
pub const ACCOUNT_IN_USE: i64 = 0;
pub const FROZEN: i64 = 17;
pub const NON_TRANSFERABLE: i64 = 37;
pub const PAUSED: i64 = 67;
/// A transfer hook program is set, and Pump's CPI does not pass its accounts.
pub const MISSING_ACCOUNT: i64 = -2;
/// Extension type the captured Token-2022 does not know.
pub const INVALID_ACCOUNT_DATA: i64 = -3;
/// The runtime's `ArithmeticOverflow` from `sub_lamports`.
pub const ARITHMETIC_OVERFLOW: i64 = -4;
pub const OVERFLOW: i64 = 6024;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: i64 = 6027;
/// The fee extension needs a writable quote mint to withdraw into, at any rate.
pub const QUOTE_MINT_NOT_WRITABLE: i64 = 6110;
/// pump_amm codes.
pub const AMM_ZERO_BASE: i64 = 6001;
pub const AMM_ZERO_QUOTE: i64 = 6002;
pub const AMM_TOO_LITTLE_LIQUIDITY: i64 = 6003;
pub const AMM_UNSUPPORTED_BASE_MINT: i64 = 6006;
pub const AMM_UNSUPPORTED_QUOTE_MINT: i64 = 6007;
pub const AMM_DISABLED_CREATE_POOL: i64 = 6017;
pub const AMM_TRUNCATION: i64 = 6024;
pub const AMM_MAYHEM_DISABLED: i64 = 6041;
pub const AMM_CASHBACK_NOT_ENABLED: i64 = 6049;

pub const TRANSFER_FEE: u16 = 1;
pub const DEFAULT_ACCOUNT_STATE: u16 = 6;
pub const NON_TRANSFERABLE_MINT: u16 = 9;
pub const TRANSFER_HOOK: u16 = 14;
pub const METADATA_POINTER: u16 = 18;
pub const TOKEN_METADATA: u16 = 19;
pub const PAUSABLE: u16 = 26;
/// Highest extension type the captured Token-2022 parses.
pub const LAST_KNOWN_EXTENSION: u16 = 28;
/// Mint extensions pump_amm rejects on the quote side. Any extension other than
/// these two is rejected on the base side.
pub const QUOTE_REJECTED: [u16; 8] = [3, 10, 20, 21, 22, 23, 24, 28];
pub const BASE_ALLOWED: [u16; 2] = [METADATA_POINTER, TOKEN_METADATA];

pub const TOKEN_ACCOUNT_RENT: u64 = 2_039_280;
pub const LP_ACCOUNT_RENT: u64 = 2_074_080;
pub const LP_MINT_RENT: u64 = 1_461_600;
pub const POOL_RENT: u64 = 2_888_400;
pub const LAMPORTS_PER_BYTE: u64 = 6_960;
pub const ACCOUNT_STORAGE_OVERHEAD: u64 = 128;
pub const TX_FEE: u64 = 5_000;
pub const MINIMUM_LIQUIDITY: u64 = 100;
pub const BOOST_DENOMINATOR: u128 = 1_000_000_000_000_000;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Route {
    Native,
    /// A curve whose `quote_mint` is the wrapped SOL mint: a token route.
    WrappedSol,
    Spl,
    Token2022,
}

/// A mint's extensions, with the three settings that change a transfer.
#[derive(Clone, Default)]
pub struct Extensions {
    pub ids: Vec<u16>,
    pub default_frozen: bool,
    pub paused: bool,
    pub hook_set: bool,
}

impl Extensions {
    fn has(&self, id: u16) -> bool {
        self.ids.contains(&id)
    }

    fn unknown(&self) -> bool {
        self.ids.iter().any(|&id| id > LAST_KNOWN_EXTENSION)
    }

    /// Length of a new associated token account of this Token-2022 mint.
    fn account_len(&self) -> u64 {
        let mut len = 170;
        for (id, size) in [(TRANSFER_FEE, 12), (NON_TRANSFERABLE_MINT, 4), (TRANSFER_HOOK, 5), (PAUSABLE, 4)] {
            if self.has(id) {
                len += size;
            }
        }
        len
    }

    fn account_rent(&self) -> u64 {
        (ACCOUNT_STORAGE_OVERHEAD + self.account_len()) * LAMPORTS_PER_BYTE
    }

    /// First transfer failure on this mint, with the frozen state of both ends.
    fn transfer(&self, amount: u64, from_frozen: bool, to_frozen: bool) -> Result<(), i64> {
        if amount == 0 {
            return Ok(());
        }
        if from_frozen {
            return Err(FROZEN);
        }
        if self.has(NON_TRANSFERABLE_MINT) {
            return Err(NON_TRANSFERABLE);
        }
        if self.paused {
            return Err(PAUSED);
        }
        if to_frozen {
            return Err(FROZEN);
        }
        if self.hook_set {
            return Err(MISSING_ACCOUNT);
        }
        Ok(())
    }
}

/// Frozen accounts, as stored before the call.
#[derive(Clone, Copy, Default)]
pub struct Frozen {
    pub curve_base: bool,
    pub curve_quote: bool,
    pub authority_mint: bool,
    pub authority_quote: bool,
    pub pool_base: bool,
    pub pool_quote: bool,
    pub vault: bool,
}

pub struct Migration {
    pub route: Route,
    pub token_2022_base: bool,
    pub base_mint: Extensions,
    pub quote_mint: Extensions,
    pub curve_tokens: u64,
    pub real_quote_reserves: u64,
    pub post_complete_quote_in: u64,
    pub pool_migration_fee: u64,
    pub curve_mayhem: bool,
    pub curve_cashback: bool,
    pub disable_create: bool,
    pub mayhem_enabled: bool,
    pub cashback_enabled: bool,
    pub boost_enabled: bool,
    pub remaining_accounts: usize,
    pub boost_vault_exists: bool,
    /// Balances of accounts that exist before the call (`None`: created here).
    pub authority_mint_account: Option<u64>,
    pub authority_quote_account: Option<u64>,
    pub pool_base_account: Option<u64>,
    pub pool_quote_account: Option<u64>,
    pub frozen: Frozen,
    pub quote_mint_writable: bool,
    pub pool_taken: bool,
    pub user_lamports: u64,
    /// Tokens missing from the curve's quote account, against its reserves.
    pub curve_quote_missing: u64,
    pub curve_lamports: u64,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Migrated {
    pub base: u64,
    pub quote: u64,
    pub initial_liquidity: u64,
    pub lp_out: u64,
    pub pool_base_after: u64,
    pub pool_quote_after: u64,
    pub boosted: u64,
    pub vault_after: u64,
    pub user_paid: u64,
    pub withdraw_gain: u64,
    pub quote_left: Option<u64>,
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

fn pay(lamports: &mut u64, amount: u64) -> Result<(), i64> {
    *lamports = lamports.checked_sub(amount).ok_or(INSUFFICIENT)?;
    Ok(())
}

pub fn migrate(m: &Migration) -> Result<Migrated, i64> {
    if m.base_mint.unknown() || m.quote_mint.unknown() {
        return Err(INVALID_ACCOUNT_DATA);
    }
    let native = m.route == Route::Native;
    // The fee leaves the curve first, as a plain lamport subtraction.
    if native && m.curve_lamports < m.pool_migration_fee {
        return Err(ARITHMETIC_OVERFLOW);
    }
    let plain_quote = !matches!(m.route, Route::Token2022);
    let quote_rent = if plain_quote { TOKEN_ACCOUNT_RENT } else { m.quote_mint.account_rent() };
    let base_rent = if m.token_2022_base { m.base_mint.account_rent() } else { TOKEN_ACCOUNT_RENT };
    let mut authority = m.pool_migration_fee;
    let mut user = m.user_lamports.saturating_sub(TX_FEE);
    let mut user_paid = 0;
    if !native {
        pay(&mut user, m.pool_migration_fee)?;
        user_paid += m.pool_migration_fee;
    }
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
                pay(&mut user, rent)?;
                user_paid += rent;
            }
        }
    }
    let base = m.authority_mint_account.unwrap_or(0) + m.curve_tokens;
    let reserves = m.real_quote_reserves.checked_add(m.post_complete_quote_in).ok_or(OVERFLOW)?;
    let quote = if native { reserves.checked_sub(m.pool_migration_fee).ok_or(OVERFLOW)? } else { reserves };
    // New accounts of a default-frozen mint start frozen.
    let new_frozen = |ext: &Extensions, account: Option<u64>, stored: bool| {
        if account.is_none() {
            ext.default_frozen
        } else {
            stored
        }
    };
    let authority_mint_frozen = new_frozen(&m.base_mint, m.authority_mint_account, m.frozen.authority_mint);
    let authority_quote_frozen = new_frozen(&m.quote_mint, m.authority_quote_account, m.frozen.authority_quote);
    let pool_base_frozen = new_frozen(&m.base_mint, m.pool_base_account, m.frozen.pool_base);
    let pool_quote_frozen = new_frozen(&m.quote_mint, m.pool_quote_account, m.frozen.pool_quote);
    m.base_mint.transfer(m.curve_tokens, m.frozen.curve_base, authority_mint_frozen)?;
    // On the native route `sync_native` does not look at the frozen state, so a
    // frozen quote account only stops pump_amm's deposit.
    if !native {
        if m.curve_quote_missing > 0 && reserves > 0 && !m.frozen.curve_quote {
            return Err(INSUFFICIENT);
        }
        m.quote_mint.transfer(reserves, m.frozen.curve_quote, authority_quote_frozen)?;
    }
    // pump_amm's `init` constraints run before any of its handler checks.
    if m.pool_taken {
        return Err(ACCOUNT_IN_USE);
    }
    pay(&mut authority, POOL_RENT)?;
    pay(&mut authority, LP_MINT_RENT)?;
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
    if m.base_mint.ids.iter().any(|id| !BASE_ALLOWED.contains(id)) {
        return Err(AMM_UNSUPPORTED_BASE_MINT);
    }
    if m.quote_mint.ids.iter().any(|id| QUOTE_REJECTED.contains(id)) {
        return Err(AMM_UNSUPPORTED_QUOTE_MINT);
    }
    m.base_mint.transfer(base, authority_mint_frozen, pool_base_frozen)?;
    m.quote_mint.transfer(quote, authority_quote_frozen, pool_quote_frozen)?;
    let pool_base_after = m.pool_base_account.unwrap_or(0) + base;
    let mut pool_quote_after = m.pool_quote_account.unwrap_or(0) + quote;
    let initial_liquidity = isqrt(pool_base_after as u128 * pool_quote_after as u128);
    if initial_liquidity < MINIMUM_LIQUIDITY {
        return Err(AMM_TOO_LITTLE_LIQUIDITY);
    }
    let (mut boosted, mut vault_after) = (0, 0);
    if !m.curve_mayhem {
        if m.remaining_accounts == 2 {
            if !m.boost_vault_exists {
                pay(&mut user, quote_rent)?;
                user_paid += quote_rent;
            }
            if m.boost_enabled {
                let amount = pool_base_after as u128 * pool_quote_after as u128 / BOOST_DENOMINATOR;
                let amount = u64::try_from(amount).map_err(|_| AMM_TRUNCATION)?;
                if amount != 0 && amount < pool_quote_after {
                    let vault_frozen = if m.boost_vault_exists { m.frozen.vault } else { m.quote_mint.default_frozen };
                    m.quote_mint.transfer(amount, pool_quote_frozen, vault_frozen)?;
                    boosted = amount;
                    pool_quote_after -= amount;
                    vault_after = amount;
                }
            }
        } else if m.boost_enabled {
            return Err(NOT_ENOUGH_REMAINING_ACCOUNTS);
        }
    }
    if m.quote_mint.has(TRANSFER_FEE) && !m.quote_mint_writable {
        return Err(QUOTE_MINT_NOT_WRITABLE);
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
