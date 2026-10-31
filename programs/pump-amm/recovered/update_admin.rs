//! PumpSwap `update_admin`.
//!
//! A pure model of which check stops the call, the bytes the `GlobalConfig`
//! account holds afterwards, and the `UpdateAdminEvent` that is logged. The
//! config is read from raw bytes the way the captured program reads it; the
//! owner, signer, writable flag and the event-authority / program addresses
//! arrive as booleans worked out by the caller. `new_admin` arrives as the
//! 32-byte address of that meta. The instruction has no Borsh arguments.
//!
//! `tests/test_pump_amm_update_admin_captured.py` runs the same inputs on
//! `evidence/original/pump_amm/deployed.so`. Agreement there is matching
//! behaviour on those inputs, not a byte-identity claim.

/// Anchor and program error numbers.
pub const INSTRUCTION_FALLBACK_NOT_FOUND: u32 = 101;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_NOT_ENOUGH_KEYS: u32 = 3005;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const ACCOUNT_NOT_SIGNER: u32 = 3010;
pub const INVALID_ADMIN: u32 = 6005;

/// `sha256("global:update_admin")[..8]`.
pub const UPDATE_ADMIN_DISCRIMINATOR: [u8; 8] = [161, 176, 40, 213, 60, 184, 179, 228];
/// `sha256("account:GlobalConfig")[..8]`.
pub const CONFIG_DISCRIMINATOR: [u8; 8] = [149, 8, 156, 202, 160, 252, 176, 217];
/// `sha256("event:UpdateAdminEvent")[..8]`.
pub const UPDATE_ADMIN_EVENT_DISCRIMINATOR: [u8; 8] = [225, 152, 171, 87, 246, 63, 66, 234];

/// Account lengths (discriminator included) at which each layout is read.
/// Under `V899` the account is `InvalidAccountData`. Missing fields read as
/// zero, and the whole `V941` struct is written back.
pub const V899: usize = 907;
pub const V932: usize = 940;
pub const V941: usize = 949;

pub const ADMIN: usize = 8;
pub const MAYHEM_MODE_ENABLED: usize = 417;
pub const IS_CASHBACK_ENABLED: usize = 642;
pub const BOOST_ENABLED: usize = 939;
pub const CREATOR_FEE_CONFIGURABLE: usize = 940;

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
    /// `site` names the missing meta when `code` is 3005, and is empty
    /// otherwise. The five missing-account failures share one error number;
    /// the captured program's Anchor log names the account.
    Error { code: u32, site: &'static str },
    InvalidAccountData,
    BorshIoError,
    /// The event was logged, then the self-CPI found no PumpSwap account.
    MissingAccountAfterEvent(Vec<u8>),
    /// The event was logged and self-CPI'd, then the write-back failed.
    BorshIoErrorAfterEvent(Vec<u8>),
    /// The new config account bytes and the logged event.
    Ok { config: Vec<u8>, event: Vec<u8> },
}

struct Config {
    head: Vec<u8>,
    tail: Vec<u8>,
}

/// `Err(None)` is `InvalidAccountData`, `Err(Some(()))` a `bool` above 1.
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
    let mut head = data[..V941.min(data.len())].to_vec();
    head.resize(V941, 0);
    if data.len() < V932 {
        head[V899..].fill(0);
    } else if data.len() < V941 {
        head[V932..].fill(0);
    }
    Ok(Config { head, tail: data.get(V941..).unwrap_or(&[]).to_vec() })
}

fn error(code: u32) -> Outcome {
    Outcome::Error { code, site: "" }
}

fn missing(site: &'static str) -> Outcome {
    Outcome::Error { code: ACCOUNT_NOT_ENOUGH_KEYS, site }
}

/// `payload` is the whole instruction data, discriminator included. Bytes
/// after the discriminator are ignored. `admin` is the first meta's address,
/// `new_admin` the third's, and `timestamp` the clock's `unix_timestamp`.
pub fn update_admin(
    payload: &[u8],
    accounts: &Accounts,
    config: &[u8],
    admin: [u8; 32],
    new_admin: [u8; 32],
    timestamp: i64,
) -> Outcome {
    // Dispatch runs before any account is looked at. A short buffer or any
    // other discriminator is the fallback error; this instruction has no args.
    if payload.len() < 8 || payload[..8] != UPDATE_ADMIN_DISCRIMINATOR {
        return error(INSTRUCTION_FALLBACK_NOT_FOUND);
    }
    if accounts.count < 1 {
        return missing("admin");
    }
    if !accounts.admin_signer {
        return error(ACCOUNT_NOT_SIGNER);
    }
    if accounts.count < 2 {
        return missing("global_config");
    }
    if !accounts.config_owner_ok {
        return error(ACCOUNT_OWNED_BY_WRONG_PROGRAM);
    }
    let mut cfg = match read_config(config) {
        Ok(cfg) => cfg,
        Err(None) => return Outcome::InvalidAccountData,
        Err(Some(())) => return Outcome::BorshIoError,
    };
    // `new_admin`, `event_authority` and `program` load next. Each missing
    // meta fails here, before `mut`, `has_one` or the seeds constraint.
    if accounts.count < 3 {
        return missing("new_admin");
    }
    if accounts.count < 4 {
        return missing("event_authority");
    }
    if accounts.count < 5 {
        return missing("program");
    }
    // Constraints: `mut`, `has_one = admin`, then the event-authority seeds.
    // The config address is not checked, and `new_admin` is not constrained.
    if !accounts.config_writable {
        return error(CONSTRAINT_MUT);
    }
    if cfg.head[ADMIN..ADMIN + 32] != admin {
        return error(INVALID_ADMIN);
    }
    if !accounts.event_authority_ok {
        return error(CONSTRAINT_SEEDS);
    }
    let mut old_admin = [0u8; 32];
    old_admin.copy_from_slice(&cfg.head[ADMIN..ADMIN + 32]);
    cfg.head[ADMIN..ADMIN + 32].copy_from_slice(&new_admin);
    let mut event = Vec::with_capacity(80);
    event.extend_from_slice(&UPDATE_ADMIN_EVENT_DISCRIMINATOR);
    event.extend_from_slice(&timestamp.to_le_bytes());
    event.extend_from_slice(&old_admin);
    event.extend_from_slice(&new_admin);
    // `emit!` logs first; `emit_cpi!` then needs the program account.
    if !accounts.program_ok {
        return Outcome::MissingAccountAfterEvent(event);
    }
    // Exit writes the whole V941 struct, so an older, shorter account fails.
    if config.len() < V941 {
        return Outcome::BorshIoErrorAfterEvent(event);
    }
    let mut out = cfg.head;
    out.extend_from_slice(&cfg.tail);
    Outcome::Ok { config: out, event }
}
