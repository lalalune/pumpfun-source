//! PumpSwap `GlobalConfig` admin toggles: `disable`, `toggle_mayhem_mode`,
//! `toggle_cashback_enabled` and `toggle_boost`.
//!
//! A pure model of which check stops the call, the bytes the config account
//! holds afterwards and the `DisableEvent` that only `disable` logs. The
//! config is read from raw bytes the way the captured program reads it; the
//! owner, signer, writable flag and the event-authority / program addresses
//! arrive as booleans worked out by the caller.
//! `tests/test_pump_amm_global_config_toggles_captured.py` runs the same inputs
//! on `evidence/original/pump_amm/deployed.so`; agreement there is matching
//! behaviour on those inputs, not a byte-identity claim.

/// Anchor and program error numbers.
pub const INSTRUCTION_DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_NOT_ENOUGH_KEYS: u32 = 3005;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const ACCOUNT_NOT_SIGNER: u32 = 3010;
pub const INVALID_ADMIN: u32 = 6005;
pub const MAYHEM_MODE_IN_DESIRED_STATE: u32 = 6043;
pub const CASHBACK_NOT_IN_DESIRED_STATE: u32 = 6051;

/// `sha256("account:GlobalConfig")[..8]`.
pub const CONFIG_DISCRIMINATOR: [u8; 8] = [149, 8, 156, 202, 160, 252, 176, 217];
/// `sha256("event:DisableEvent")[..8]`.
pub const DISABLE_EVENT_DISCRIMINATOR: [u8; 8] = [107, 253, 193, 76, 228, 202, 27, 104];

/// Account lengths (discriminator included) at which each layout is read.
/// Under `V899` the account is `InvalidAccountData`. `V899` stops after
/// `buyback_basis_points`, `V932` adds `boost_authority` and `boost_enabled`,
/// `V941` adds `creator_fee_configurable` and `max_configurable_creator_fee_bps`.
/// Missing fields read as zero.
pub const V899: usize = 907;
pub const V932: usize = 940;
pub const V941: usize = 949;

pub const ADMIN: usize = 8;
pub const DISABLE_FLAGS: usize = 56;
pub const MAYHEM_MODE_ENABLED: usize = 417;
pub const IS_CASHBACK_ENABLED: usize = 642;
pub const BOOST_AUTHORITY: usize = 907;
pub const BOOST_ENABLED: usize = 939;
pub const CREATOR_FEE_CONFIGURABLE: usize = 940;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    Disable,
    ToggleMayhemMode,
    ToggleCashbackEnabled,
    ToggleBoost,
}

impl Kind {
    /// `toggle_boost` takes only `admin` and `global_config`; the other three
    /// are `#[event_cpi]` and also take `event_authority` and `program`.
    pub fn accounts(self) -> usize {
        if self == Kind::ToggleBoost { 2 } else { 4 }
    }
    fn arg_count(self) -> usize {
        if self == Kind::Disable { 5 } else { 1 }
    }
}

/// Account-level facts that need the runtime or an address comparison.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Accounts {
    /// How many account metas the instruction carries.
    pub count: usize,
    /// `admin` signed the transaction.
    pub admin_signer: bool,
    /// `global_config` is owned by PumpSwap.
    pub config_owner_ok: bool,
    /// `global_config` is passed writable.
    pub config_writable: bool,
    /// `event_authority` is `["__event_authority"]` of PumpSwap.
    pub event_authority_ok: bool,
    /// `program` is PumpSwap itself.
    pub program_ok: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    Error(u32),
    InvalidAccountData,
    BorshIoError,
    /// `disable` logged its event, then the self-CPI found no PumpSwap account.
    MissingAccountAfterEvent(Vec<u8>),
    /// `disable` logged and self-CPI'd its event, then the write-back failed.
    BorshIoErrorAfterEvent(Vec<u8>),
    /// The new config account bytes and the logged event (empty if none).
    Ok { config: Vec<u8>, event: Vec<u8> },
}

/// Every field the program reads from and writes back to a `GlobalConfig`.
/// The two `bool` fields kept as raw bytes are only ever 0 or 1 once read.
struct Config {
    head: Vec<u8>,
    tail: Vec<u8>,
}

/// Reads the config. `Err(None)` is `InvalidAccountData`, `Err(Some(()))` a
/// `bool` above 1 (`BorshIoError`).
fn read_config(data: &[u8]) -> Result<Config, Option<()>> {
    if data.len() < V899 || data[..8] != CONFIG_DISCRIMINATOR {
        return Err(None);
    }
    let mut bools = vec![MAYHEM_MODE_ENABLED, IS_CASHBACK_ENABLED];
    if data.len() >= V932 {
        bools.push(BOOST_ENABLED);
    }
    if data.len() >= V941 {
        bools.push(CREATOR_FEE_CONFIGURABLE);
    }
    if bools.iter().any(|&at| data[at] > 1) {
        return Err(Some(()));
    }
    // The serialized struct is always the V941 layout; fields the version
    // lacks read as zero.
    let mut head = data[..V941.min(data.len())].to_vec();
    head.resize(V941, 0);
    if data.len() < V932 {
        head[V899..].fill(0);
    } else if data.len() < V941 {
        head[V932..].fill(0);
    }
    Ok(Config { head, tail: data.get(V941..).unwrap_or(&[]).to_vec() })
}

/// Anchor's Borsh arguments: `bool`s must be 0 or 1; trailing bytes are ignored.
fn read_args(kind: Kind, payload: &[u8]) -> Option<Vec<u8>> {
    let n = kind.arg_count();
    if payload.len() < n || payload[..n].iter().any(|&b| b > 1) {
        return None;
    }
    Some(payload[..n].to_vec())
}

pub fn global_config_toggle(
    kind: Kind,
    payload: &[u8],
    accounts: &Accounts,
    config: &[u8],
    admin: [u8; 32],
    timestamp: i64,
) -> Outcome {
    // Instruction arguments are decoded before any account is looked at.
    let args = match read_args(kind, payload) {
        Some(a) => a,
        None => return Outcome::Error(INSTRUCTION_DID_NOT_DESERIALIZE),
    };
    // Accounts load in order; a missing meta fails when its account is reached.
    if accounts.count < 1 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if !accounts.admin_signer {
        return Outcome::Error(ACCOUNT_NOT_SIGNER);
    }
    if accounts.count < 2 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if !accounts.config_owner_ok {
        return Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM);
    }
    let mut cfg = match read_config(config) {
        Ok(c) => c,
        Err(None) => return Outcome::InvalidAccountData,
        Err(Some(())) => return Outcome::BorshIoError,
    };
    if accounts.count < kind.accounts() {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    // Constraints: `mut`, `has_one = admin`, then the event-authority seeds.
    // The config address itself is not checked.
    if !accounts.config_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if cfg.head[ADMIN..ADMIN + 32] != admin {
        return Outcome::Error(INVALID_ADMIN);
    }
    if kind != Kind::ToggleBoost && !accounts.event_authority_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    let mut event = Vec::new();
    match kind {
        Kind::ToggleMayhemMode => {
            if cfg.head[MAYHEM_MODE_ENABLED] == args[0] {
                return Outcome::Error(MAYHEM_MODE_IN_DESIRED_STATE);
            }
            cfg.head[MAYHEM_MODE_ENABLED] = args[0];
        }
        Kind::ToggleCashbackEnabled => {
            if cfg.head[IS_CASHBACK_ENABLED] == args[0] {
                return Outcome::Error(CASHBACK_NOT_IN_DESIRED_STATE);
            }
            cfg.head[IS_CASHBACK_ENABLED] = args[0];
        }
        Kind::ToggleBoost => {
            // Setting the current value is allowed; a zero boost authority is not.
            if cfg.head[BOOST_AUTHORITY..BOOST_AUTHORITY + 32] == [0u8; 32] {
                return Outcome::Error(INVALID_ADMIN);
            }
            cfg.head[BOOST_ENABLED] = args[0];
        }
        Kind::Disable => {
            // Bits 0..4 are create-pool, deposit, withdraw, buy, sell; bits 5..7 are kept.
            let mut flags = cfg.head[DISABLE_FLAGS] & !0x1f;
            for (bit, &on) in args.iter().enumerate() {
                flags |= on << bit;
            }
            cfg.head[DISABLE_FLAGS] = flags;
            event.extend_from_slice(&DISABLE_EVENT_DISCRIMINATOR);
            event.extend_from_slice(&timestamp.to_le_bytes());
            event.extend_from_slice(&admin);
            event.extend_from_slice(&args);
            // `emit!` logs first; `emit_cpi!` then needs the program account.
            if !accounts.program_ok {
                return Outcome::MissingAccountAfterEvent(event);
            }
        }
    }
    // Exit writes the whole V941 struct, so an older, shorter account fails.
    if config.len() < V941 {
        return if event.is_empty() { Outcome::BorshIoError } else { Outcome::BorshIoErrorAfterEvent(event) };
    }
    let mut out = cfg.head;
    out.extend_from_slice(&cfg.tail);
    Outcome::Ok { config: out, event }
}
