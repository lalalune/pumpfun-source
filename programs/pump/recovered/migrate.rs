//! Captured Pump-side rules of `migrate` (native-SOL curve to a PumpSwap
//! pool): the account checks, the authority / quote / completion gates, the
//! already-migrated early return, the quote amount handed to pump_amm
//! `create_pool`, the creator flags it carries, the boost gate that reads
//! pump_amm's GlobalConfig, and the curve after the move.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_migrate_captured.py`. pump_amm itself is replaced there by a
//! no-op program, so only what Pump decides is modelled; the pool contents
//! are pump_amm's business. Not linked into the SBF crate. This is not a
//! byte-identity claim.
//!
//! Unconfirmed (outside the checked inputs): a non-zero base-token balance
//! (create_pool's `base_amount_in`, always 0 here), a curve holding less than
//! `real_quote_reserves + post_complete_quote_in + Rent::minimum_balance(166)`
//! lamports, a `pool_migration_fee` below 10,000,000 or above the curve's
//! lamports, and Token-2022 base mints.

pub const NOT_AUTHORIZED: u32 = 6000;
pub const BONDING_CURVE_NOT_COMPLETE: u32 = 6006;
pub const OVERFLOW: u32 = 6024;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: u32 = 6027;
pub const UNSUPPORTED_QUOTE_MINT: u32 = 6063;
/// Anchor `ConstraintMut`.
pub const CONSTRAINT_MUT: u32 = 2000;
/// Anchor `ConstraintSeeds`.
pub const CONSTRAINT_SEEDS: u32 = 2006;
/// Anchor `ConstraintAddress`.
pub const CONSTRAINT_ADDRESS: u32 = 2012;
/// pump_amm GlobalConfig byte read as `boost_enabled`.
pub const BOOST_ENABLED_OFFSET: usize = 939;

/// One wrong account. Checked in IDL account order, before the handler; the
/// order of pairs not exercised by the test is unconfirmed.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Fault {
    /// `withdraw_authority != global.withdraw_authority`.
    WithdrawAuthority,
    /// `withdraw_authority` passed read-only.
    WithdrawReadonly,
    /// `bonding_curve.quote_mint != Pubkey::default()` (a curve constraint,
    /// so it comes before the later accounts and before the completion gate).
    CurveQuoteMint,
    /// `pool` is not the canonical pump_amm pool PDA (index 0).
    Pool,
    /// `amm_global_config` is not pump_amm's `global_config` PDA.
    AmmGlobalConfig,
    /// `wsol_mint` is another initialized mint (it seeds the WSOL ATA).
    WsolMint,
    /// `lp_mint` is not the pool's LP-mint PDA.
    LpMint,
    /// `pump_amm_event_authority` is not pump_amm's event-authority PDA.
    AmmEventAuthority,
    /// `rent` is not the rent sysvar.
    Rent,
}

impl Fault {
    pub fn code(self) -> u32 {
        match self {
            Fault::WithdrawAuthority => NOT_AUTHORIZED,
            Fault::WithdrawReadonly => CONSTRAINT_MUT,
            Fault::CurveQuoteMint => UNSUPPORTED_QUOTE_MINT,
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

pub struct Migrate {
    pub faults: Vec<Fault>,
    /// Raw `complete` byte.
    pub complete: u8,
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub post_complete_quote_in: u64,
    pub pool_migration_fee: u64,
    pub is_mayhem_mode: bool,
    pub is_cashback_coin: bool,
    pub creator_fee_bps: u64,
    pub can_edit_creator_fee: bool,
    pub is_holder_reward: bool,
    pub amm_config: Option<AmmConfig>,
    pub remaining_accounts: usize,
    /// Curve lamports above `real_quote_reserves + post_complete_quote_in`.
    pub curve_slack: u64,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    /// Borsh rejects a `complete` byte above 1 while loading the curve.
    InvalidBool,
}

/// The `create_pool` arguments Pump sends (index is always 0).
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
    AlreadyMigrated,
    Migrated {
        pool: CreatePool,
        /// `init_boost` was called with the two remaining accounts.
        init_boost: bool,
        /// Curve lamports afterwards; the reserves are zeroed.
        curve_lamports: u64,
    },
}

pub fn boost_enabled(config: &Option<AmmConfig>) -> bool {
    // Short or wrongly tagged data reads as disabled, and so does a byte of 2
    // (bytes above 2 are unconfirmed).
    match config {
        Some(c) => c.len > BOOST_ENABLED_OFFSET && c.discriminator_ok && c.boost_byte == 1,
        None => false,
    }
}

pub fn migrate(m: &Migrate) -> Result<Outcome, Stop> {
    if m.complete > 1 {
        return Err(Stop::InvalidBool);
    }
    if let Some(f) = m.faults.iter().min() {
        return Err(Stop::Code(f.code()));
    }
    if m.complete == 0 {
        return Err(Stop::Code(BONDING_CURVE_NOT_COMPLETE));
    }
    if m.virtual_token_reserves == 0
        && m.virtual_quote_reserves == 0
        && m.real_token_reserves == 0
        && m.real_quote_reserves == 0
    {
        return Ok(Outcome::AlreadyMigrated);
    }
    // `Global.enable_migrate` is not read here.
    // Added first, so post_complete_quote_in can cover a reserve below the fee.
    let quote = m
        .real_quote_reserves
        .checked_add(m.post_complete_quote_in)
        .and_then(|q| q.checked_sub(m.pool_migration_fee))
        .ok_or(Stop::Code(OVERFLOW))?;
    let pool = CreatePool {
        quote_amount_in: quote,
        is_mayhem_mode: m.is_mayhem_mode,
        is_cashback_coin: m.is_cashback_coin,
        creator_fee_bps: m.creator_fee_bps,
        can_edit_creator_fee: m.can_edit_creator_fee,
        is_holder_reward: m.is_holder_reward,
    };
    // The boost step runs after create_pool and is skipped for mayhem curves.
    // Exactly two remaining accounts call init_boost whatever the config says;
    // any other count is rejected only while boost is enabled.
    let init_boost = !m.is_mayhem_mode && m.remaining_accounts == 2;
    if !m.is_mayhem_mode && !init_boost && boost_enabled(&m.amm_config) {
        return Err(Stop::Code(NOT_ENOUGH_REMAINING_ACCOUNTS));
    }
    Ok(Outcome::Migrated { pool, init_boost, curve_lamports: m.curve_slack })
}
