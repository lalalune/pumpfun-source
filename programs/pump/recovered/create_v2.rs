//! Captured rules of Pump `create_v2` (Token-2022 mint, optional quote mint,
//! optional mayhem mode): the optional-argument decoding, the account checks,
//! the argument gates, how the quote mint is admitted, the reserves of a
//! single-curve nested quote, and the bonding curve and supply it produces.
//!
//! The creator fee rule is `create_fee_bounds.rs`, repeated here only so the
//! gates keep their order. Checked against `evidence/original/pump/deployed.so`
//! and the captured SPL Token, Token-2022, Associated Token and Mayhem programs
//! by `tests/test_create_v2_captured.py`. Not linked into the SBF crate. This
//! is not a byte-identity claim.
//!
//! Unconfirmed (outside the checked inputs): quote chains of two or more
//! curves, pool records, Token-2022 quote mint extensions, and the rent paid.

pub const INSTRUCTION_DID_NOT_DESERIALIZE: u32 = 102;
/// Anchor `ConstraintMut`, `ConstraintSeeds`, `ConstraintAddress`.
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const CONSTRAINT_ADDRESS: u32 = 2012;
/// Anchor `AccountDidNotDeserialize`, `InvalidProgramId`, `AccountNotInitialized`.
pub const ACCOUNT_DID_NOT_DESERIALIZE: u32 = 3003;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const ACCOUNT_NOT_INITIALIZED: u32 = 3012;
/// System program `AccountAlreadyInUse` (the mint `init`).
pub const ACCOUNT_ALREADY_IN_USE: u32 = 0;
/// Token-2022 `Overflow` (the second mint of a mayhem coin).
pub const TOKEN_OVERFLOW: u32 = 14;
pub const OVERFLOW: u32 = 6024;
pub const DIVISION_BY_ZERO: u32 = 6026;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: u32 = 6027;
pub const CREATOR_SHOULD_NOT_BE_ZERO: u32 = 6030;
pub const NAME_TOO_LONG: u32 = 6043;
pub const SYMBOL_TOO_LONG: u32 = 6044;
pub const URI_TOO_LONG: u32 = 6045;
pub const CREATE_V2_DISABLED: u32 = 6046;
pub const MAYHEM_MODE_DISABLED: u32 = 6048;
pub const UNSUPPORTED_QUOTE_MINT: u32 = 6063;
pub const INVALID_QUOTE_TOKEN_PROGRAM: u32 = 6064;
pub const INVALID_ASSOCIATED_QUOTE_BONDING_CURVE: u32 = 6065;
pub const MAYHEM_MODE_QUOTE_MINT_NOT_ALLOWED: u32 = 6071;
pub const INVALID_QUOTE_CONTROL: u32 = 6075;
pub const CREATOR_FEE_NOT_CONFIGURABLE: u32 = 6077;
pub const CREATOR_FEE_BPS_OUT_OF_RANGE: u32 = 6078;
pub const CASHBACK_DEPRECATED: u32 = 6082;
pub const HOLDER_REWARD_DISABLED: u32 = 6084;
pub const INVALID_QUOTE_BONDING_CURVE: u32 = 6099;
pub const QUOTE_BONDING_CURVE_NOT_ELIGIBLE: u32 = 6100;
pub const QUOTE_POOL_ACCOUNTS_REQUIRED: u32 = 6101;
pub const QUOTE_RESERVES_OUT_OF_RANGE: u32 = 6104;
pub const CURVE_DEPTH_EXCEEDED: u32 = 6105;
pub const QUOTE_CURVE_AWAITING_MIGRATION: u32 = 6107;
pub const QUOTE_CHAIN_ACCOUNTS_REQUIRED: u32 = 6109;
pub const MAX_NAME_BYTES: usize = 32;
pub const MAX_SYMBOL_BYTES: usize = 13;
pub const MAX_URI_BYTES: usize = 200;

/// One wrong account, earliest check first: the account loads, the three
/// `init`s, then the remaining constraints. Variants with the same result can
/// not be told apart by their order, so theirs is unconfirmed.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Fault {
    /// `global` is an empty account.
    GlobalMissing,
    /// `global` data fails to load (an `initialized` byte of 2).
    GlobalBadBool,
    SystemProgram,
    TokenProgram,
    AssociatedTokenProgram,
    /// `mint` is already an initialized account.
    MintInUse,
    BondingCurve,
    /// `associated_bonding_curve` is not the mint's curve ATA: its `init` CPI
    /// names an account the transaction did not pass.
    CurveAta,
    MintAuthority,
    MayhemProgram,
    GlobalParams,
    SolVault,
    MayhemState,
    EventAuthority,
    /// A mayhem `mut` account passed read-only. Its place among the other
    /// faults is unconfirmed.
    MayhemReadOnly,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    /// The runtime's `MissingAccount`, raised inside the ATA `init` CPI.
    MissingAccount,
    /// `IllegalOwner` from the ATA program: the quote ATA already exists.
    IllegalOwner,
}

impl Fault {
    pub fn stop(self) -> Stop {
        Stop::Code(match self {
            Fault::GlobalMissing => ACCOUNT_NOT_INITIALIZED,
            Fault::GlobalBadBool => ACCOUNT_DID_NOT_DESERIALIZE,
            Fault::SystemProgram | Fault::TokenProgram | Fault::AssociatedTokenProgram => INVALID_PROGRAM_ID,
            Fault::MintInUse => ACCOUNT_ALREADY_IN_USE,
            Fault::CurveAta => return Stop::MissingAccount,
            Fault::MayhemProgram => CONSTRAINT_ADDRESS,
            Fault::MayhemReadOnly => CONSTRAINT_MUT,
            _ => CONSTRAINT_SEEDS,
        })
    }
}

/// The `Global` fields `create_v2` reads.
#[derive(Clone, Debug)]
pub struct Global {
    pub create_v2_enabled: bool,
    pub mayhem_mode_enabled: bool,
    pub is_holder_reward_enabled: bool,
    pub creator_fee_configurable: bool,
    pub max_configurable_creator_fee_bps: u64,
    pub max_curve_depth: u8,
    pub initial_virtual_token_reserves: u64,
    pub initial_virtual_sol_reserves: u64,
    pub initial_real_token_reserves: u64,
    pub token_total_supply: u64,
    pub initial_virtual_quote_reserves: u64,
    pub pool_migration_fee: u64,
}

/// What seeds the price of a nested quote: the quote of the root curve.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Root {
    Sol,
    Whitelisted,
    Listed(u64),
    Unlisted,
}

/// The quote mint's own bonding curve.
#[derive(Clone, Copy, Debug)]
pub struct QuoteCurve {
    pub depth: u8,
    pub mayhem: bool,
    pub complete: bool,
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub token_total_supply: u64,
    pub root: Root,
}

/// The remaining accounts, as the admission walk sees them.
#[derive(Clone, Copy, Debug)]
pub enum Quote {
    /// No remaining accounts.
    None,
    /// One or two remaining accounts.
    TooFewAccounts,
    /// `remaining_accounts[2]` is not SPL Token or Token-2022.
    WrongProgram,
    /// The right key, not executable.
    ProgramNotExecutable,
    /// The native mint or the default key.
    NativeMint,
    /// The one mint the program rejects outright.
    BlockedMint,
    Whitelisted,
    /// A QuoteControl entry with these initial reserves (0 is stored as is).
    Listed(u64),
    ControlAbsent,
    ControlWrongKey,
    ControlWrongOwner,
    /// Valid QuoteControl, no entry, no quote curve passed.
    Unlisted,
    /// Wrong key, wrong owner or undecodable data.
    QuoteCurveInvalid,
    QuoteCurve(QuoteCurve),
}

pub struct Create {
    pub faults: Vec<Fault>,
    /// The required `is_mayhem_mode` byte.
    pub mayhem_byte: u8,
    /// Instruction bytes after `is_mayhem_mode`.
    pub tail: Vec<u8>,
    pub creator_is_zero: bool,
    /// UTF-8 byte lengths of the three strings.
    pub name_bytes: usize,
    pub symbol_bytes: usize,
    pub uri_bytes: usize,
    pub quote: Quote,
    /// The quote mint's owner is not `remaining_accounts[2]`.
    pub quote_owner_wrong: bool,
    pub quote_ata_wrong: bool,
    /// The curve's quote ATA already exists; the ATA program refuses it.
    pub quote_ata_exists: bool,
    /// Mayhem's `global_params` exists (only a mayhem create reads it).
    pub mayhem_params: bool,
    pub global: Global,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum QuoteMint {
    Default,
    /// The mint in `remaining_accounts[0]`.
    Passed,
}

/// The new bonding curve (fields not listed are zero / false).
#[derive(Debug, PartialEq, Eq)]
pub struct Curve {
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub token_total_supply: u64,
    pub initial_virtual_quote_reserves: u64,
    pub quote_mint: QuoteMint,
    pub creator_fee_bps: u64,
    pub depth: u8,
    pub mayhem: bool,
    /// The creator is the `holder-rewards` PDA of the mint.
    pub holder_reward: bool,
    /// Total minted: the supply, twice for a mayhem coin.
    pub minted: u64,
    /// The curve's quote ATA was created.
    pub quote_ata: bool,
}

/// `is_cashback_enabled`, `creator_fee_bps`, `is_holder_reward`. Missing bytes
/// read as false or 0. A fee shorter than 8 bytes reads as 0 and consumes
/// nothing, so its first byte is then the holder flag.
pub fn decode_tail(tail: &[u8]) -> Result<(bool, u64, bool), u32> {
    let flag = |byte: Option<&u8>| match byte {
        None | Some(0) => Ok(false),
        Some(1) => Ok(true),
        Some(_) => Err(INSTRUCTION_DID_NOT_DESERIALIZE),
    };
    let cashback = flag(tail.first())?;
    let rest = tail.get(1..).unwrap_or(&[]);
    let (fee, rest) = match rest.split_first_chunk::<8>() {
        Some((bytes, rest)) => (u64::from_le_bytes(*bytes), rest),
        None => (0, rest),
    };
    Ok((cashback, fee, flag(rest.first())?))
}

/// `amount_in * base / (quote + amount_in)`.
fn constant_product(base: u64, quote: u128, amount: u128) -> Result<u128, u32> {
    if quote == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    let denominator = quote.checked_add(amount).ok_or(OVERFLOW)?;
    let numerator = (base as u128).checked_mul(amount).ok_or(OVERFLOW)?;
    Ok(numerator / denominator)
}

/// Reserves of a quote mint whose curve is an unmigrated root curve. The
/// initial buy of the seed amount is priced through the curve, past its
/// completion into the pool it would migrate to, and scaled back.
fn nested_reserves(q: &QuoteCurve, seed: u64, pool_base: u64, g: &Global) -> Result<u64, u32> {
    let real = g.initial_real_token_reserves as u128;
    let difference = (g.initial_virtual_token_reserves as u128).checked_sub(real).ok_or(OVERFLOW)?;
    let amount = (real * seed as u128).checked_div(difference).ok_or(DIVISION_BY_ZERO)?;
    let (vt, vq, rt) = (q.virtual_token_reserves as u128, q.virtual_quote_reserves as u128, q.real_token_reserves as u128);
    let mut output = constant_product(q.virtual_token_reserves, vq, amount)?;
    if output > rt {
        let denominator = vt.checked_sub(rt).ok_or(OVERFLOW)?;
        if denominator == 0 {
            return Err(DIVISION_BY_ZERO);
        }
        let completion = rt * vq / denominator + 1;
        let remainder = amount.saturating_sub(completion);
        output = rt;
        if remainder > 1 {
            let migration_fee = if q.root == Root::Sol { g.pool_migration_fee as u128 } else { 0 };
            let pool_quote = (completion + q.real_quote_reserves as u128).checked_sub(migration_fee).ok_or(OVERFLOW)?;
            output = rt.checked_add(constant_product(pool_base, pool_quote, remainder - 1)?).ok_or(OVERFLOW)?;
        }
    }
    let quotient = output.checked_mul(difference).ok_or(OVERFLOW)?.checked_div(real).ok_or(DIVISION_BY_ZERO)?;
    let reserves = u64::try_from(quotient).map_err(|_| OVERFLOW)?;
    if reserves == 0 {
        return Err(QUOTE_RESERVES_OUT_OF_RANGE);
    }
    Ok(reserves)
}

/// The admission walk for one quote curve: returns (reserves, depth).
fn walk(q: &QuoteCurve, g: &Global) -> Result<(u64, u8), u32> {
    let depth = q.depth.checked_add(1).ok_or(OVERFLOW)?;
    if depth > g.max_curve_depth.min(5) {
        return Err(CURVE_DEPTH_EXCEEDED);
    }
    if q.mayhem {
        return Err(QUOTE_BONDING_CURVE_NOT_ELIGIBLE);
    }
    // A root curve seeds the price before its own record is read.
    let seed = match (q.depth, q.root) {
        (0, Root::Sol) => g.initial_virtual_sol_reserves,
        (0, Root::Whitelisted) => g.initial_virtual_quote_reserves,
        (0, Root::Listed(reserves)) => reserves,
        (0, Root::Unlisted) => return Err(QUOTE_BONDING_CURVE_NOT_ELIGIBLE),
        _ => 0,
    };
    let empty = q.real_quote_reserves == 0
        && q.virtual_quote_reserves == 0
        && q.real_token_reserves == 0
        && q.virtual_token_reserves == 0;
    if empty {
        // Only the curve was passed; a migrated curve is priced from its pool.
        return Err(QUOTE_POOL_ACCOUNTS_REQUIRED);
    }
    if q.complete {
        return Err(QUOTE_CURVE_AWAITING_MIGRATION);
    }
    let pool_base = q.token_total_supply.checked_sub(g.initial_real_token_reserves).ok_or(OVERFLOW)?;
    if q.depth != 0 {
        return Err(QUOTE_CHAIN_ACCOUNTS_REQUIRED);
    }
    Ok((nested_reserves(q, seed, pool_base, g)?, depth))
}

pub fn create_v2(c: &Create) -> Result<Curve, Stop> {
    let code = Stop::Code;
    // Arguments decode before any account is looked at.
    if c.mayhem_byte > 1 {
        return Err(code(INSTRUCTION_DID_NOT_DESERIALIZE));
    }
    let mayhem = c.mayhem_byte == 1;
    let (cashback, requested_fee, holder_reward) = decode_tail(&c.tail).map_err(code)?;
    if let Some(f) = c.faults.iter().min() {
        return Err(f.stop());
    }
    let g = &c.global;
    if mayhem && !g.mayhem_mode_enabled {
        return Err(code(MAYHEM_MODE_DISABLED));
    }
    if cashback {
        return Err(code(CASHBACK_DEPRECATED));
    }
    if holder_reward && !g.is_holder_reward_enabled {
        return Err(code(HOLDER_REWARD_DISABLED));
    }
    // The holder PDA replaces the creator argument, so a zero one is fine.
    if c.creator_is_zero && !holder_reward {
        return Err(code(CREATOR_SHOULD_NOT_BE_ZERO));
    }
    if !g.create_v2_enabled {
        return Err(code(CREATE_V2_DISABLED));
    }
    // (stored reserves, quote mint, whether a fee counts, whether mayhem may
    // use this quote, depth)
    let (reserves, quote_mint, counted, global_quote, depth) = match c.quote {
        Quote::None | Quote::NativeMint => {
            (g.initial_virtual_sol_reserves, QuoteMint::Default, false, true, 0)
        }
        Quote::TooFewAccounts => return Err(code(NOT_ENOUGH_REMAINING_ACCOUNTS)),
        Quote::WrongProgram | Quote::ProgramNotExecutable => return Err(code(INVALID_QUOTE_TOKEN_PROGRAM)),
        Quote::BlockedMint | Quote::ControlAbsent | Quote::Unlisted => return Err(code(UNSUPPORTED_QUOTE_MINT)),
        Quote::ControlWrongKey | Quote::ControlWrongOwner => return Err(code(INVALID_QUOTE_CONTROL)),
        Quote::QuoteCurveInvalid => return Err(code(INVALID_QUOTE_BONDING_CURVE)),
        Quote::Whitelisted => (g.initial_virtual_quote_reserves, QuoteMint::Passed, false, true, 0),
        Quote::Listed(reserves) => (reserves, QuoteMint::Passed, true, false, 0),
        Quote::QuoteCurve(q) => {
            let (reserves, depth) = walk(&q, g).map_err(code)?;
            (reserves, QuoteMint::Passed, true, false, depth)
        }
    };
    let quote_ata = quote_mint == QuoteMint::Passed;
    if quote_ata {
        if c.quote_owner_wrong {
            return Err(code(UNSUPPORTED_QUOTE_MINT));
        }
        if c.quote_ata_wrong {
            return Err(code(INVALID_ASSOCIATED_QUOTE_BONDING_CURVE));
        }
        if c.quote_ata_exists {
            return Err(Stop::IllegalOwner);
        }
    }
    if mayhem && !global_quote {
        return Err(code(MAYHEM_MODE_QUOTE_MINT_NOT_ALLOWED));
    }
    let mut creator_fee_bps = 0;
    if counted && requested_fee != 0 {
        if !g.creator_fee_configurable {
            return Err(code(CREATOR_FEE_NOT_CONFIGURABLE));
        }
        if requested_fee > g.max_configurable_creator_fee_bps {
            return Err(code(CREATOR_FEE_BPS_OUT_OF_RANGE));
        }
        creator_fee_bps = requested_fee;
    }
    if c.name_bytes > MAX_NAME_BYTES {
        return Err(code(NAME_TOO_LONG));
    }
    if c.symbol_bytes > MAX_SYMBOL_BYTES {
        return Err(code(SYMBOL_TOO_LONG));
    }
    if c.uri_bytes > MAX_URI_BYTES {
        return Err(code(URI_TOO_LONG));
    }
    if mayhem && !c.mayhem_params {
        // Raised by the Mayhem program inside its CPI.
        return Err(code(ACCOUNT_NOT_INITIALIZED));
    }
    // No check against the reserves: the whole supply is minted, and a mayhem
    // coin mints it again to the Mayhem vault.
    let minted = if mayhem {
        g.token_total_supply.checked_mul(2).ok_or(code(TOKEN_OVERFLOW))?
    } else {
        g.token_total_supply
    };
    Ok(Curve {
        virtual_token_reserves: g.initial_virtual_token_reserves,
        virtual_quote_reserves: reserves,
        real_token_reserves: g.initial_real_token_reserves,
        token_total_supply: g.token_total_supply,
        initial_virtual_quote_reserves: reserves,
        quote_mint,
        creator_fee_bps,
        depth,
        mayhem,
        holder_reward,
        minted,
        quote_ata,
    })
}
