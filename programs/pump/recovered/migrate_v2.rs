//! Captured Pump-side rules of `migrate_v2` (a native-SOL or SPL-token quote
//! curve to a PumpSwap pool): the account checks, the curve rent top-up, the
//! pump_amm event-authority check, the completion gate and already-migrated
//! early return, the migration fee route, the quote amount handed to pump_amm
//! `create_pool`, the creator flags it carries, the boost gate, and the curve
//! and its quote vault after the move.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_migrate_v2_captured.py`. pump_amm itself is replaced there by
//! a no-op program, so only what Pump decides is modelled; the pool contents
//! are pump_amm's business. Not linked into the SBF crate. This is not a
//! byte-identity claim.
//!
//! Unconfirmed (outside the checked inputs): a non-zero base-token balance,
//! Token-2022 base or quote mints (transfer fees, the harvest before the
//! quote-account close, `QuoteMintNotWritable`), pre-existing pool or pool
//! authority token accounts on the native route, a curve shorter than 166
//! bytes, and a failure after a non-zero rent top-up (LiteSVM reports those
//! as a rent error on another account, so the test keeps them out).

pub const NOT_AUTHORIZED: u32 = 6000;
pub const MINT_DOES_NOT_MATCH_BONDING_CURVE: u32 = 6004;
pub const BONDING_CURVE_NOT_COMPLETE: u32 = 6006;
pub const OVERFLOW: u32 = 6024;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: u32 = 6027;
/// Anchor `ConstraintMut`.
pub const CONSTRAINT_MUT: u32 = 2000;
/// Anchor `ConstraintSeeds`.
pub const CONSTRAINT_SEEDS: u32 = 2006;
/// Anchor `ConstraintAddress`.
pub const CONSTRAINT_ADDRESS: u32 = 2012;
/// System `transfer` with too few lamports (raised through the ATA program).
pub const INSUFFICIENT_LAMPORTS: u32 = 1;
/// SPL Token `InsufficientFunds`.
pub const INSUFFICIENT_TOKENS: u32 = 1;
/// pump_amm GlobalConfig byte read as `boost_enabled`.
pub const BOOST_ENABLED_OFFSET: usize = 939;
/// `Rent::minimum_balance(166)`, the bonding-curve size.
pub const CURVE_RENT: u64 = 2_046_240;
/// Rent of one 165-byte SPL token account.
pub const TOKEN_ACCOUNT_RENT: u64 = 2_039_280;
/// Token accounts the pool authority creates and pays for on the native route
/// (pool base, pool quote, its own base and WSOL accounts).
pub const NATIVE_CREATED_ACCOUNTS: u64 = 4;

/// One wrong account. Checked in IDL account order, before the handler; the
/// order of pairs not exercised by the test is unconfirmed. The pump_amm
/// event authority is checked later, inside the handler.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Fault {
    /// `withdraw_authority != global.withdraw_authority`.
    WithdrawAuthority,
    /// `withdraw_authority` passed read-only.
    WithdrawReadonly,
    /// `quote_mint` is neither the curve's quote mint nor WSOL for a native curve.
    QuoteMint,
    /// `associated_quote_bonding_curve` is not the curve's quote ATA.
    CurveQuoteAccount,
    /// `pool` is not the canonical pump_amm pool PDA (index 0).
    Pool,
    /// `pool_authority_quote_account` is not the pool authority's quote ATA.
    PoolAuthorityQuoteAccount,
    /// `amm_global_config` is not pump_amm's `global_config` PDA.
    AmmGlobalConfig,
    /// `lp_mint` is not the pool's LP-mint PDA.
    LpMint,
    /// `pool_quote_token_account` is not the pool's quote ATA.
    PoolQuoteAccount,
    /// `rent` is not the rent sysvar.
    Rent,
}

impl Fault {
    pub fn code(self) -> u32 {
        match self {
            Fault::WithdrawAuthority => NOT_AUTHORIZED,
            Fault::WithdrawReadonly => CONSTRAINT_MUT,
            Fault::QuoteMint => MINT_DOES_NOT_MATCH_BONDING_CURVE,
            Fault::Rent => CONSTRAINT_ADDRESS,
            _ => CONSTRAINT_SEEDS,
        }
    }
}

/// pump_amm `GlobalConfig` as Pump sees it (owner is not checked).
pub struct AmmConfig {
    pub len: usize,
    pub discriminator_ok: bool,
    pub boost_byte: u8,
}

pub struct MigrateV2 {
    pub faults: Vec<Fault>,
    /// `pump_amm_event_authority` is not pump_amm's event-authority PDA.
    pub wrong_amm_event_authority: bool,
    /// The curve has a quote mint (SPL token) rather than the default (native).
    pub token_quote: bool,
    /// Raw `complete` byte.
    pub complete: u8,
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub post_complete_quote_in: u64,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    pub pool_migration_fee: u64,
    pub is_mayhem_mode: bool,
    pub is_cashback_coin: bool,
    pub creator_fee_bps: u64,
    pub can_edit_creator_fee: bool,
    pub is_holder_reward: bool,
    pub amm_config: Option<AmmConfig>,
    pub remaining_accounts: usize,
    pub curve_lamports: u64,
    /// Token balance of the curve's quote ATA (token route only).
    pub quote_vault: u64,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    /// Borsh rejects a `complete` byte above 1 while loading the curve.
    InvalidBool,
    /// `sub_lamports` on the curve went below zero.
    ArithmeticOverflow,
    /// The curve ends between zero and its rent-exempt minimum.
    CurveBelowRent,
}

/// The `create_pool` arguments Pump sends (index and base amount are 0 here).
#[derive(Debug, PartialEq, Eq)]
pub struct CreatePool {
    pub quote_amount_in: u64,
    pub is_mayhem_mode: bool,
    pub is_cashback_coin: bool,
    pub creator_fee_bps: u64,
    pub can_edit_creator_fee: bool,
    pub is_holder_reward: bool,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Outcome {
    /// Complete curve with all four reserves zero: returns Ok, no CPI, no event.
    AlreadyMigrated { curve_lamports: u64 },
    Migrated {
        pool: CreatePool,
        /// `init_boost` was called with the two remaining accounts.
        init_boost: bool,
        /// Curve lamports afterwards (0 = the account is gone); the reserves are zeroed.
        curve_lamports: u64,
        /// Token balance left in the curve's quote ATA.
        quote_vault: u64,
    },
}

pub fn boost_enabled(config: &Option<AmmConfig>) -> bool {
    match config {
        Some(c) => c.len > BOOST_ENABLED_OFFSET && c.discriminator_ok && c.boost_byte == 1,
        None => false,
    }
}

/// `prepare_bonding_curve`: the user tops the curve up to the rent minimum of
/// 166 bytes. A native curve keeps `real_quote_reserves + creator_fee +
/// protocol_fees` out of the balance it counts; `post_complete_quote_in` is
/// not reserved.
fn rent_top_up(m: &MigrateV2) -> Result<u64, Stop> {
    let reserved = if m.token_quote {
        0
    } else {
        let fees = m.creator_fee.checked_add(m.protocol_fees).ok_or(Stop::Code(OVERFLOW))?;
        m.real_quote_reserves.checked_add(fees).ok_or(Stop::Code(OVERFLOW))?
    };
    Ok(CURVE_RENT.saturating_sub(m.curve_lamports.saturating_sub(reserved)))
}

pub fn migrate_v2(m: &MigrateV2) -> Result<Outcome, Stop> {
    if m.complete > 1 {
        return Err(Stop::InvalidBool);
    }
    if let Some(f) = m.faults.iter().min() {
        return Err(Stop::Code(f.code()));
    }
    let lamports = m.curve_lamports + rent_top_up(m)?;
    if m.wrong_amm_event_authority {
        return Err(Stop::Code(CONSTRAINT_SEEDS));
    }
    if m.complete == 0 {
        return Err(Stop::Code(BONDING_CURVE_NOT_COMPLETE));
    }
    if m.virtual_token_reserves == 0
        && m.virtual_quote_reserves == 0
        && m.real_token_reserves == 0
        && m.real_quote_reserves == 0
    {
        return Ok(Outcome::AlreadyMigrated { curve_lamports: lamports });
    }
    // Native: the fee leaves the curve for the pool authority, which then pays
    // the rent of the four token accounts it creates. Token route: the user
    // pays the fee and the account rent.
    let fee = m.pool_migration_fee;
    if !m.token_quote {
        if lamports < fee {
            return Err(Stop::ArithmeticOverflow);
        }
        if fee < NATIVE_CREATED_ACCOUNTS * TOKEN_ACCOUNT_RENT {
            return Err(Stop::Code(INSUFFICIENT_LAMPORTS));
        }
    }
    let gross = m
        .real_quote_reserves
        .checked_add(m.post_complete_quote_in)
        .ok_or(Stop::Code(OVERFLOW))?;
    let quote = if m.token_quote { gross } else { gross.checked_sub(fee).ok_or(Stop::Code(OVERFLOW))? };
    let (curve_lamports, quote_vault) = if m.token_quote {
        // transfer_checked is skipped for 0.
        if m.quote_vault < quote {
            return Err(Stop::Code(INSUFFICIENT_TOKENS));
        }
        (lamports, m.quote_vault - quote)
    } else {
        (lamports - fee).checked_sub(quote).map(|l| (l, 0)).ok_or(Stop::ArithmeticOverflow)?
    };
    let pool = CreatePool {
        quote_amount_in: quote,
        is_mayhem_mode: m.is_mayhem_mode,
        is_cashback_coin: m.is_cashback_coin,
        creator_fee_bps: m.creator_fee_bps,
        can_edit_creator_fee: m.can_edit_creator_fee,
        is_holder_reward: m.is_holder_reward,
    };
    // After create_pool; skipped for mayhem curves. Exactly two remaining
    // accounts call init_boost whatever the config says.
    let init_boost = !m.is_mayhem_mode && m.remaining_accounts == 2;
    if !m.is_mayhem_mode && !init_boost && boost_enabled(&m.amm_config) {
        return Err(Stop::Code(NOT_ENOUGH_REMAINING_ACCOUNTS));
    }
    // Checked by the runtime when the instruction ends.
    if curve_lamports != 0 && curve_lamports < CURVE_RENT {
        return Err(Stop::CurveBelowRent);
    }
    Ok(Outcome::Migrated { pool, init_boost, curve_lamports, quote_vault })
}
