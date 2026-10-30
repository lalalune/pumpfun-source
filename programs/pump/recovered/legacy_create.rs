//! Captured rules of the legacy Pump `create` (SPL Token mint + Metaplex
//! metadata, native-SOL curve): the account checks, the zero-creator gate,
//! the Metaplex string limits it runs into, and the bonding curve, minted
//! supply and CreateEvent it produces from `Global`.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured
//! token-metadata program by `tests/test_legacy_create_captured.py`. Not
//! linked into the SBF crate. This is not a byte-identity claim.
//!
//! Unconfirmed (outside the checked inputs): Token-2022 or mayhem variants
//! (that is `create_v2`), and how much rent the metadata account takes.

pub const CREATOR_SHOULD_NOT_BE_ZERO: u32 = 6030;
/// Anchor `ConstraintSeeds`.
pub const CONSTRAINT_SEEDS: u32 = 2006;
/// Anchor `AccountNotInitialized`.
pub const ACCOUNT_NOT_INITIALIZED: u32 = 3012;
/// Anchor `AccountDidNotDeserialize`.
pub const ACCOUNT_DID_NOT_DESERIALIZE: u32 = 3003;
/// System program `AccountAlreadyInUse` (the mint `init`).
pub const ACCOUNT_ALREADY_IN_USE: u32 = 0;
/// Token Metadata `NameTooLong`, `SymbolTooLong`, `UriTooLong`.
pub const NAME_TOO_LONG: u32 = 11;
pub const SYMBOL_TOO_LONG: u32 = 12;
pub const URI_TOO_LONG: u32 = 13;
pub const MAX_NAME_BYTES: usize = 32;
pub const MAX_SYMBOL_BYTES: usize = 10;
pub const MAX_URI_BYTES: usize = 200;

/// One wrong account. The Global load fails first; then the `init` and seed
/// checks run in IDL account order. The order of pairs not exercised by the
/// test is unconfirmed.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Fault {
    /// `global` is an empty account.
    GlobalMissing,
    /// `global` data fails to load (an `initialized` byte of 2).
    GlobalBadBool,
    /// `mint` is already an initialized account (system-owned and funded is fine).
    MintInUse,
    /// `mint_authority` is not the `mint-authority` PDA.
    MintAuthority,
    /// `bonding_curve` is not the curve PDA of the mint.
    BondingCurve,
    /// `metadata` is not the Metaplex metadata PDA of the mint.
    Metadata,
}

impl Fault {
    pub fn code(self) -> u32 {
        match self {
            Fault::MintInUse => ACCOUNT_ALREADY_IN_USE,
            Fault::GlobalMissing => ACCOUNT_NOT_INITIALIZED,
            Fault::GlobalBadBool => ACCOUNT_DID_NOT_DESERIALIZE,
            _ => CONSTRAINT_SEEDS,
        }
    }
}

/// The `Global` fields `create` copies.
pub struct Global {
    pub initial_virtual_token_reserves: u64,
    pub initial_virtual_sol_reserves: u64,
    pub initial_real_token_reserves: u64,
    pub token_total_supply: u64,
}

pub struct Create {
    pub faults: Vec<Fault>,
    /// UTF-8 byte lengths of the three strings.
    pub name_bytes: usize,
    pub symbol_bytes: usize,
    pub uri_bytes: usize,
    pub creator_is_zero: bool,
    pub global: Global,
}

/// The new bonding curve (fields not listed are zero / false / default).
#[derive(Debug, PartialEq, Eq)]
pub struct Curve {
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub token_total_supply: u64,
    pub initial_virtual_quote_reserves: u64,
    /// Minted to the curve's ATA; the mint authority is then revoked.
    pub minted: u64,
}

pub fn create(c: &Create) -> Result<Curve, u32> {
    if let Some(f) = c.faults.iter().min() {
        return Err(f.code());
    }
    // `Global.initialized` is not read.
    if c.creator_is_zero {
        return Err(CREATOR_SHOULD_NOT_BE_ZERO);
    }
    // The metadata CPI comes next and checks its strings in this order.
    if c.name_bytes > MAX_NAME_BYTES {
        return Err(NAME_TOO_LONG);
    }
    if c.symbol_bytes > MAX_SYMBOL_BYTES {
        return Err(SYMBOL_TOO_LONG);
    }
    if c.uri_bytes > MAX_URI_BYTES {
        return Err(URI_TOO_LONG);
    }
    let g = &c.global;
    Ok(Curve {
        virtual_token_reserves: g.initial_virtual_token_reserves,
        virtual_quote_reserves: g.initial_virtual_sol_reserves,
        real_token_reserves: g.initial_real_token_reserves,
        token_total_supply: g.token_total_supply,
        initial_virtual_quote_reserves: g.initial_virtual_sol_reserves,
        // No check against the reserves: the whole supply is minted.
        minted: g.token_total_supply,
    })
}
