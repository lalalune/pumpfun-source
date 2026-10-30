//! PumpSwap `set_coin_creator`: fill in a canonical pool's empty coin creator
//! from the token's Metaplex metadata, or from its Pump bonding curve when the
//! metadata lists no creators.
//!
//! A pure model of which check stops the call, the bytes the pool account
//! holds afterwards and the event the program logs. The account layouts are
//! read from raw bytes the way the captured program reads them; PDA
//! comparisons and owners arrive as booleans worked out by the caller.
//! `tests/test_pump_amm_set_coin_creator_captured.py` runs the same inputs on
//! `evidence/original/pump_amm/deployed.so`; agreement there is matching
//! behaviour on those inputs, not a byte-identity claim.
//!
//! Resource-sensitive outcomes require an independently calibrated metadata
//! heap budget supplied by the caller. Account count, duplicate account keys
//! and caller/runtime layout can change that budget. This model accounts for
//! the three string allocations but does not simulate creator-Vec allocation;
//! creator-list cases are supported only when that allocation fits. It is not
//! a general heap model or a proof for arbitrary account configurations.

/// Anchor and program error numbers.
pub const INSTRUCTION_FALLBACK_NOT_FOUND: u32 = 101;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const ACCOUNT_DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const ACCOUNT_DID_NOT_DESERIALIZE: u32 = 3003;
pub const ACCOUNT_NOT_ENOUGH_KEYS: u32 = 3005;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const ONLY_CANONICAL_PUMP_POOLS_CAN_HAVE_COIN_CREATOR: u32 = 6028;

/// `sha256("account:Pool")[..8]`.
pub const POOL_DISCRIMINATOR: [u8; 8] = [0xf1, 0x9a, 0x6d, 0x04, 0x11, 0xb1, 0x6d, 0xbc];
/// `sha256("account:BondingCurve")[..8]`.
pub const CURVE_DISCRIMINATOR: [u8; 8] = [0x17, 0xb7, 0xf8, 0x37, 0x60, 0xd8, 0xac, 0x60];
/// `sha256("event:SetMetaplexCoinCreatorEvent")[..8]`.
pub const METAPLEX_EVENT_DISCRIMINATOR: [u8; 8] = [150, 107, 199, 123, 124, 207, 102, 228];
/// `sha256("event:SetBondingCurveCoinCreatorEvent")[..8]`.
pub const CURVE_EVENT_DISCRIMINATOR: [u8; 8] = [242, 231, 235, 102, 65, 99, 189, 211];
/// Metaplex `Key::MetadataV1`.
pub const METADATA_V1: u8 = 4;

/// Bytes a pool needs before the program will read it: discriminator through
/// `lp_supply`. A later field that is cut short reads as zero, even when some
/// of its bytes are present.
pub const POOL_READABLE: usize = 211;
/// Bytes the program writes back: the whole serialized `Pool`.
pub const POOL_SERIALIZED: usize = 287;
pub const COIN_CREATOR: usize = 211;
pub const BASE_MINT: usize = 43;
/// The four `bool` fields of `Pool`: mayhem, cashback, can-edit, holder-reward.
pub const POOL_BOOLS: [usize; 4] = [243, 244, 269, 270];
/// `(offset, width)` of every `Pool` field after `lp_supply`.
pub const POOL_TAIL: [(usize, usize); 9] =
    [(211, 32), (243, 1), (244, 1), (245, 16), (261, 8), (269, 1), (270, 1), (271, 8), (279, 8)];
/// `BondingCurve`: discriminator, five `u64`, `complete`, creator, two bools.
pub const CURVE_LEN: usize = 83;
pub const CURVE_CREATOR: usize = 49;
pub const CURVE_BOOLS: [usize; 3] = [48, 81, 82];

/// Account-level facts that need a PDA derivation or the runtime.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Accounts {
    /// How many account metas the instruction carries.
    pub count: usize,
    /// `pool` is owned by PumpSwap.
    pub pool_owner_ok: bool,
    /// `pool` is passed writable.
    pub pool_writable: bool,
    /// `pool.creator` is Pump's `["pool-authority", pool.base_mint]`.
    pub pool_canonical: bool,
    /// `metadata` is owned by Metaplex Token Metadata.
    pub metadata_owner_ok: bool,
    /// `metadata` is Metaplex's `["metadata", program, pool.base_mint]`.
    pub metadata_seeds_ok: bool,
    /// `bonding_curve` is owned by Pump.
    pub curve_owner_ok: bool,
    /// `bonding_curve` is Pump's `["bonding-curve", pool.base_mint]`.
    pub curve_seeds_ok: bool,
    /// `event_authority` is PumpSwap's `["__event_authority"]`.
    pub event_seeds_ok: bool,
    /// `program` is the executable PumpSwap program, so the `emit_cpi!` self-call lands.
    pub program_ok: bool,
    /// Independently admitted free bytes before metadata string allocation.
    /// This is context-specific, not inferred from account count alone.
    pub metadata_heap_free: usize,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    /// Failed before anything was logged. Numbers are Anchor or program errors.
    Error(u32),
    /// A runtime error before anything was logged.
    InvalidAccountData,
    BorshIoError,
    /// A panic or a failed allocation.
    ProgramFailedToComplete,
    /// The event was logged and then the call failed, so nothing is committed.
    MissingAccountAfterEvent(Vec<u8>),
    BorshIoErrorAfterEvent(Vec<u8>),
    /// The pool already had a coin creator: committed with no event.
    AlreadySet { pool: Vec<u8> },
    /// Committed: the new pool bytes and the logged event.
    Set { pool: Vec<u8>, event: Vec<u8> },
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

/// A Borsh reader over the metadata bytes.
struct Reader<'a> {
    data: &'a [u8],
    at: usize,
    heap: usize,
}

impl Reader<'_> {
    fn take(&mut self, n: usize) -> Result<&[u8], Outcome> {
        if self.data.len() - self.at < n {
            return Err(Outcome::BorshIoError);
        }
        self.at += n;
        Ok(&self.data[self.at - n..self.at])
    }

    fn byte(&mut self) -> Result<u8, Outcome> {
        Ok(self.take(1)?[0])
    }

    fn flag(&mut self) -> Result<bool, Outcome> {
        match self.byte()? {
            0 => Ok(false),
            1 => Ok(true),
            _ => Err(Outcome::BorshIoError),
        }
    }

    fn u32(&mut self) -> Result<usize, Outcome> {
        let b = self.take(4)?;
        Ok(u32::from_le_bytes([b[0], b[1], b[2], b[3]]) as usize)
    }

    fn string(&mut self) -> Result<(), Outcome> {
        let len = self.u32()?;
        if len > self.heap {
            return Err(Outcome::ProgramFailedToComplete);
        }
        self.heap -= len;
        let text = self.take(len)?;
        if std::str::from_utf8(text).is_err() {
            return Err(Outcome::BorshIoError);
        }
        Ok(())
    }
}

/// Metaplex `Metadata` read through `edition_nonce`; everything after it is
/// read leniently and cannot fail. Returns the creators' addresses, if the
/// list is present.
fn read_metadata(data: &[u8], heap_free: usize) -> Result<Option<Vec<[u8; 32]>>, Outcome> {
    if data.first() != Some(&METADATA_V1) {
        return Err(Outcome::BorshIoError);
    }
    let mut r = Reader { data, at: 1, heap: heap_free };
    r.take(64)?; // update authority, mint
    for _ in 0..3 {
        r.string()?; // name, symbol, uri
    }
    r.take(2)?; // seller fee basis points
    let creators = if r.flag()? {
        let count = r.u32()?;
        let mut out = Vec::new();
        for _ in 0..count {
            let address = key(r.take(32)?, 0);
            r.flag()?; // verified
            r.byte()?; // share
            out.push(address);
        }
        Some(out)
    } else {
        None
    };
    r.flag()?; // primary sale happened
    r.flag()?; // is mutable
    if r.flag()? {
        r.byte()?; // edition nonce
    }
    Ok(creators)
}

fn read_curve(data: &[u8]) -> Result<[u8; 32], u32> {
    if data.len() < 8 {
        return Err(ACCOUNT_DISCRIMINATOR_NOT_FOUND);
    }
    if data[..8] != CURVE_DISCRIMINATOR {
        return Err(ACCOUNT_DISCRIMINATOR_MISMATCH);
    }
    if data.len() < CURVE_LEN || CURVE_BOOLS.iter().any(|&at| data[at] > 1) {
        return Err(ACCOUNT_DID_NOT_DESERIALIZE);
    }
    Ok(key(data, CURVE_CREATOR))
}

/// `payload_len` is the instruction data length (the discriminator is checked
/// by the caller); the keys are the accounts' addresses and `timestamp` the
/// clock's `unix_timestamp`. `accounts.metadata_heap_free` is a caller-admitted
/// context fact; creator-list allocation must fit (see module-level limits).
#[allow(clippy::too_many_arguments)]
pub fn set_coin_creator(
    payload_len: usize,
    accounts: &Accounts,
    pool_data: &[u8],
    metadata_data: &[u8],
    curve_data: &[u8],
    pool_key: [u8; 32],
    metadata_key: [u8; 32],
    curve_key: [u8; 32],
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
    if !accounts.metadata_owner_ok {
        return Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM);
    }
    let creators = match read_metadata(metadata_data, accounts.metadata_heap_free) {
        Ok(creators) => creators,
        Err(outcome) => return outcome,
    };
    if accounts.count < 3 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if !accounts.curve_owner_ok {
        return Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM);
    }
    let curve_creator = match read_curve(curve_data) {
        Ok(creator) => creator,
        Err(code) => return Outcome::Error(code),
    };
    if accounts.count < 5 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    // Constraints: the pool has no seeds, only `mut`.
    if !accounts.pool_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if !accounts.metadata_seeds_ok || !accounts.curve_seeds_ok || !accounts.event_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    // Handler.
    if !accounts.pool_canonical {
        return Outcome::Error(ONLY_CANONICAL_PUMP_POOLS_CAN_HAVE_COIN_CREATOR);
    }
    let base_mint = key(&pool, BASE_MINT);
    let event = if key(&pool, COIN_CREATOR) != [0u8; 32] {
        None
    } else {
        let (disc, source, creator) = match &creators {
            Some(list) => match list.first() {
                Some(first) => (METAPLEX_EVENT_DISCRIMINATOR, metadata_key, *first),
                None => return Outcome::ProgramFailedToComplete,
            },
            None => (CURVE_EVENT_DISCRIMINATOR, curve_key, curve_creator),
        };
        pool[COIN_CREATOR..COIN_CREATOR + 32].copy_from_slice(&creator);
        let mut event = disc.to_vec();
        event.extend_from_slice(&timestamp.to_le_bytes());
        event.extend_from_slice(&base_mint);
        event.extend_from_slice(&pool_key);
        event.extend_from_slice(&source);
        event.extend_from_slice(&creator);
        if !accounts.program_ok {
            return Outcome::MissingAccountAfterEvent(event);
        }
        Some(event)
    };
    // Exit: the whole struct is written back over the front of the account.
    if pool_data.len() < POOL_SERIALIZED {
        return match event {
            Some(event) => Outcome::BorshIoErrorAfterEvent(event),
            None => Outcome::BorshIoError,
        };
    }
    let mut out = pool_data.to_vec();
    out[..POOL_SERIALIZED].copy_from_slice(&pool);
    match event {
        Some(event) => Outcome::Set { pool: out, event },
        None => Outcome::AlreadySet { pool: out },
    }
}
