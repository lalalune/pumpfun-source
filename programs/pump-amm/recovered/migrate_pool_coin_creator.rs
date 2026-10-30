//! PumpSwap `migrate_pool_coin_creator`: hand a pool's coin-creator fees to the
//! Pump Fees `SharingConfig` of its base mint.
//!
//! A pure model of which check stops the call, the bytes the pool account
//! holds afterwards and the `MigratePoolCoinCreatorEvent` the program logs.
//! The account layouts are read from raw bytes the way the captured program
//! reads them; PDA comparisons and owners arrive as booleans worked out by the
//! caller. `tests/test_pump_amm_migrate_pool_coin_creator_captured.py` runs the
//! same inputs on `evidence/original/pump_amm/deployed.so`; agreement there is
//! matching behaviour on those inputs, not a byte-identity claim.

/// Anchor and program error numbers.
pub const INSTRUCTION_FALLBACK_NOT_FOUND: u32 = 101;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const ACCOUNT_DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const ACCOUNT_DID_NOT_DESERIALIZE: u32 = 3003;
pub const ACCOUNT_NOT_ENOUGH_KEYS: u32 = 3005;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_SHARING_CONFIG_BASE_MINT: u32 = 6045;
pub const INVALID_SHARING_CONFIG_COIN_CREATOR: u32 = 6046;
pub const HOLDER_REWARD_CREATOR_IMMUTABLE: u32 = 6074;
pub const CREATOR_FEES_NOT_SWEPT: u32 = 6081;
pub const ONLY_CANONICAL_PUMP_POOLS_CAN_HAVE_COIN_CREATOR: u32 = 6028;

/// `sha256("account:Pool")[..8]`.
pub const POOL_DISCRIMINATOR: [u8; 8] = [0xf1, 0x9a, 0x6d, 0x04, 0x11, 0xb1, 0x6d, 0xbc];
/// `sha256("account:SharingConfig")[..8]`.
pub const SHARING_DISCRIMINATOR: [u8; 8] = [0xd8, 0x4a, 0x09, 0x00, 0x38, 0x8c, 0x5d, 0x4b];
/// `sha256("event:MigratePoolCoinCreatorEvent")[..8]`.
pub const EVENT_DISCRIMINATOR: [u8; 8] = [0xaa, 0xdd, 0x52, 0xc7, 0x93, 0xa5, 0xf7, 0x2e];

/// Bytes a pool needs before the program will read it: discriminator through
/// `lp_supply`. A later field that is cut short reads as zero, even when some
/// of its bytes are present.
pub const POOL_READABLE: usize = 211;
/// Bytes the program writes back: the whole serialized `Pool`.
pub const POOL_SERIALIZED: usize = 287;
pub const COIN_CREATOR: usize = 211;
pub const BASE_MINT: usize = 43;
pub const CREATOR_FEES: usize = 279;
pub const IS_HOLDER_REWARD: usize = 270;
/// The four `bool` fields of `Pool`: mayhem, cashback, can-edit, holder-reward.
pub const POOL_BOOLS: [usize; 4] = [243, 244, 269, 270];
/// `(offset, width)` of every `Pool` field after `lp_supply`.
pub const POOL_TAIL: [(usize, usize); 9] =
    [(211, 32), (243, 1), (244, 1), (245, 16), (261, 8), (269, 1), (270, 1), (271, 8), (279, 8)];

/// Account-level facts that need a PDA derivation or the runtime.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Accounts {
    /// How many account metas the instruction carries.
    pub count: usize,
    /// `pool` is owned by PumpSwap.
    pub pool_owner_ok: bool,
    /// `pool` is passed writable.
    pub pool_writable: bool,
    /// `pool.creator` is Pump's `["pool-authority", pool.base_mint]`, i.e. a
    /// pool that a Pump curve migrated into.
    pub pool_canonical: bool,
    /// `pool` is `["pool", index, creator, base_mint, quote_mint]` read from its own data.
    pub pool_seeds_ok: bool,
    /// `sharing_config` is owned by Pump Fees.
    pub sharing_owner_ok: bool,
    /// `sharing_config` is Pump Fees' `["sharing-config", pool.base_mint]`.
    pub sharing_seeds_ok: bool,
    /// `event_authority` is PumpSwap's `["__event_authority"]`.
    pub event_seeds_ok: bool,
    /// `program` is the executable PumpSwap program, so the `emit_cpi!` self-call lands.
    pub program_ok: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    /// Failed before anything was logged. Numbers are Anchor or program errors.
    Error(u32),
    /// A runtime error before anything was logged.
    InvalidAccountData,
    BorshIoError,
    /// The event was logged and then the call failed, so nothing is committed.
    MissingAccountAfterEvent(Vec<u8>),
    BorshIoErrorAfterEvent(Vec<u8>),
    /// Committed: the new pool bytes and the logged event.
    Migrated { pool: Vec<u8>, event: Vec<u8> },
}

fn key(data: &[u8], at: usize) -> [u8; 32] {
    let mut out = [0u8; 32];
    out.copy_from_slice(&data[at..at + 32]);
    out
}

/// The pool as the program sees it: a zero-filled copy of the serialized
/// struct, or why it cannot be read.
fn read_pool(data: &[u8]) -> Result<Vec<u8>, Outcome> {
    if data.len() < POOL_READABLE || data[..8] != POOL_DISCRIMINATOR {
        return Err(Outcome::InvalidAccountData);
    }
    let mut pool = vec![0u8; POOL_SERIALIZED];
    pool[..POOL_READABLE].copy_from_slice(&data[..POOL_READABLE]);
    for &(at, width) in POOL_TAIL.iter().filter(|&&(at, width)| at + width <= data.len()) {
        pool[at..at + width].copy_from_slice(&data[at..at + width]);
    }
    if POOL_BOOLS.iter().any(|&at| pool[at] > 1) {
        return Err(Outcome::BorshIoError);
    }
    Ok(pool)
}

/// `SharingConfig`: bump, version, status (enum of two), mint, admin,
/// admin_revoked (bool), then a `Vec` of 34-byte shareholders.
fn read_sharing(data: &[u8]) -> Result<([u8; 32], [u8; 32]), u32> {
    if data.len() < 8 {
        return Err(ACCOUNT_DISCRIMINATOR_NOT_FOUND);
    }
    if data[..8] != SHARING_DISCRIMINATOR {
        return Err(ACCOUNT_DISCRIMINATOR_MISMATCH);
    }
    if data.len() < 80 || data[10] > 1 || data[75] > 1 {
        return Err(ACCOUNT_DID_NOT_DESERIALIZE);
    }
    let count = u32::from_le_bytes([data[76], data[77], data[78], data[79]]) as usize;
    if (data.len() - 80) / 34 < count {
        return Err(ACCOUNT_DID_NOT_DESERIALIZE);
    }
    Ok((key(data, 11), key(data, 43)))
}

/// `payload_len` is the instruction data length (the discriminator is checked
/// by the caller); `sharing_key` is the `sharing_config` address and
/// `timestamp` the clock's `unix_timestamp`.
pub fn migrate_pool_coin_creator(
    payload_len: usize,
    accounts: &Accounts,
    pool_data: &[u8],
    sharing_data: &[u8],
    pool_key: [u8; 32],
    sharing_key: [u8; 32],
    timestamp: i64,
) -> Outcome {
    if payload_len < 8 {
        return Outcome::Error(INSTRUCTION_FALLBACK_NOT_FOUND);
    }
    // Account loading, in field order; a missing meta fails where it is needed.
    if accounts.count < 1 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if !accounts.pool_owner_ok {
        return Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM);
    }
    let mut pool = match read_pool(pool_data) {
        Ok(pool) => pool,
        Err(outcome) => return outcome,
    };
    if accounts.count < 2 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if !accounts.sharing_owner_ok {
        return Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM);
    }
    let (sharing_mint, sharing_admin) = match read_sharing(sharing_data) {
        Ok(fields) => fields,
        Err(code) => return Outcome::Error(code),
    };
    if accounts.count < 4 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    // Constraints, account by account: pool, then sharing_config, then
    // event_authority. Each account's seeds come before its other checks.
    let base_mint = key(&pool, BASE_MINT);
    let old_creator = key(&pool, COIN_CREATOR);
    if !accounts.pool_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.pool_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if !accounts.pool_canonical {
        return Outcome::Error(ONLY_CANONICAL_PUMP_POOLS_CAN_HAVE_COIN_CREATOR);
    }
    if !accounts.sharing_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if sharing_mint != base_mint {
        return Outcome::Error(INVALID_SHARING_CONFIG_BASE_MINT);
    }
    if old_creator != sharing_admin {
        return Outcome::Error(INVALID_SHARING_CONFIG_COIN_CREATOR);
    }
    if !accounts.event_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    // Handler.
    if pool[IS_HOLDER_REWARD] == 1 {
        return Outcome::Error(HOLDER_REWARD_CREATOR_IMMUTABLE);
    }
    if pool[CREATOR_FEES..CREATOR_FEES + 8] != [0u8; 8] {
        return Outcome::Error(CREATOR_FEES_NOT_SWEPT);
    }
    pool[COIN_CREATOR..COIN_CREATOR + 32].copy_from_slice(&sharing_key);
    let mut event = EVENT_DISCRIMINATOR.to_vec();
    event.extend_from_slice(&timestamp.to_le_bytes());
    event.extend_from_slice(&base_mint);
    event.extend_from_slice(&pool_key);
    event.extend_from_slice(&sharing_key);
    event.extend_from_slice(&old_creator);
    event.extend_from_slice(&sharing_key);
    if !accounts.program_ok {
        return Outcome::MissingAccountAfterEvent(event);
    }
    // Exit: the whole struct is written back over the front of the account.
    if pool_data.len() < POOL_SERIALIZED {
        return Outcome::BorshIoErrorAfterEvent(event);
    }
    let mut out = pool_data.to_vec();
    out[..POOL_SERIALIZED].copy_from_slice(&pool);
    Outcome::Migrated { pool: out, event }
}
