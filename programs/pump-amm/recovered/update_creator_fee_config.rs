//! PumpSwap `update_creator_fee_config`.
//!
//! A pure model of which check stops the call, the bytes and lamports the
//! `GlobalConfig` account holds afterwards, the lamports left on `admin`, and
//! the `UpdateCreatorFeeConfigEvent` that is logged. The config is read from
//! raw bytes the way the captured program reads it. Owners, the signer and
//! writable flags, whether the config account exists, and the system /
//! event-authority / program addresses arrive as facts worked out by the
//! caller.
//!
//! `tests/test_pump_amm_update_creator_fee_config_captured.py` runs the same
//! inputs on `evidence/original/pump_amm/deployed.so`. Agreement there is
//! matching behaviour on those inputs, not a byte-identity claim.

/// Anchor and program error numbers.
pub const INSTRUCTION_DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_NOT_ENOUGH_KEYS: u32 = 3005;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const ACCOUNT_NOT_SIGNER: u32 = 3010;
pub const ACCOUNT_NOT_INITIALIZED: u32 = 3012;
pub const INVALID_ADMIN: u32 = 6005;
/// System-program `Transfer` custom error: the payer's balance is short.
pub const INSUFFICIENT_LAMPORTS: u32 = 1;

/// `sha256("account:GlobalConfig")[..8]`.
pub const CONFIG_DISCRIMINATOR: [u8; 8] = [149, 8, 156, 202, 160, 252, 176, 217];
/// `sha256("event:UpdateCreatorFeeConfigEvent")[..8]`.
pub const UPDATE_CREATOR_FEE_CONFIG_EVENT_DISCRIMINATOR: [u8; 8] =
    [0x98, 0xc6, 0x7c, 0x7c, 0x6a, 0xf6, 0x7f, 0xbf];

/// Account lengths (discriminator included) at which each layout is read.
/// Under `V899` the account is `InvalidAccountData`. Missing fields read as
/// zero, and the whole `V941` struct is written back. A shorter account is
/// reallocated to `V941` before that write.
pub const V899: usize = 907;
pub const V932: usize = 940;
pub const V941: usize = 949;

pub const ADMIN: usize = 8;
pub const MAYHEM_MODE_ENABLED: usize = 417;
pub const IS_CASHBACK_ENABLED: usize = 642;
pub const BOOST_ENABLED: usize = 939;
pub const CREATOR_FEE_CONFIGURABLE: usize = 940;
pub const MAX_CONFIGURABLE_CREATOR_FEE_BPS: usize = 941;

/// Borsh size of `(bool, u64)`, before any ignored trailing bytes.
const ARG_LEN: usize = 1 + 8;

/// Account-level facts that need the runtime or an address comparison.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Accounts {
    /// How many account metas the instruction carries.
    pub count: usize,
    /// `admin` signed the transaction.
    pub admin_signer: bool,
    /// `global_config` exists. A meta whose account was never created is
    /// `AccountNotInitialized`, which is not the same as a wrong owner.
    pub config_present: bool,
    /// `global_config` is owned by PumpSwap.
    pub config_owner_ok: bool,
    /// `admin` is passed writable.
    pub admin_writable: bool,
    /// `global_config` is passed writable.
    pub config_writable: bool,
    /// `system_program` is the system program.
    pub system_ok: bool,
    /// `event_authority` is `["__event_authority"]` of PumpSwap.
    pub event_authority_ok: bool,
    /// `program` is PumpSwap itself.
    pub program_ok: bool,
    /// `admin` is owned by the system program. Only the rent top-up reads this.
    pub admin_system_owner: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    /// `site` names the account for 2000 and 3005, and is empty otherwise.
    /// Those two numbers are shared by every account that fails them.
    Error { code: u32, site: &'static str },
    InvalidAccountData,
    BorshIoError,
    /// System `Transfer` rejected a `from` account that holds data.
    /// `transfer` is the lamport amount the CPI asked for. Nothing is committed.
    FromCarriesData { transfer: u64 },
    /// System `Transfer` custom error 1. `transfer` is the amount asked for.
    InsufficientLamports { transfer: u64 },
    /// System `Transfer` was asked to debit an account the system program does
    /// not own. `transfer` is the amount asked for. Nothing is committed.
    ExternalAccountLamportSpend { transfer: u64 },
    /// The event was logged and, when `transfer` is non-zero, the rent top-up
    /// CPI was issued, then `emit_cpi!` found no PumpSwap account. The
    /// transaction rolls the lamports and the bytes back.
    MissingAccountAfterEvent { event: Vec<u8>, transfer: u64 },
    /// Committed config bytes, logged event, and the lamports afterwards.
    Ok {
        config: Vec<u8>,
        event: Vec<u8>,
        config_lamports: u64,
        admin_lamports: u64,
    },
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
    // The serialized struct is always the V941 layout. Fields a shorter
    // layout does not store read as zero, so the bytes past that layout are
    // not kept.
    let mut head = data[..V941.min(data.len())].to_vec();
    head.resize(V941, 0);
    if data.len() < V932 {
        head[V899..].fill(0);
    } else if data.len() < V941 {
        head[V932..].fill(0);
    }
    Ok(Config { head, tail: data.get(V941..).unwrap_or(&[]).to_vec() })
}

/// `creator_fee_configurable: bool`, then `max_configurable_creator_fee_bps: u64`.
/// A short payload or a bool above 1 does not deserialize. Trailing bytes are ignored.
fn read_args(payload: &[u8]) -> Option<(bool, u64)> {
    if payload.len() < ARG_LEN {
        return None;
    }
    let flag = match payload[0] {
        0 => false,
        1 => true,
        _ => return None,
    };
    Some((flag, u64::from_le_bytes(payload[1..9].try_into().unwrap())))
}

fn event_bytes(timestamp: i64, admin: [u8; 32], flag: bool, bps: u64) -> Vec<u8> {
    let mut event = Vec::with_capacity(57);
    event.extend_from_slice(&UPDATE_CREATOR_FEE_CONFIG_EVENT_DISCRIMINATOR);
    event.extend_from_slice(&timestamp.to_le_bytes());
    event.extend_from_slice(&admin);
    event.push(u8::from(flag));
    event.extend_from_slice(&bps.to_le_bytes());
    event
}

pub fn update_creator_fee_config(
    payload: &[u8],
    accounts: &Accounts,
    config: &[u8],
    admin: [u8; 32],
    timestamp: i64,
    config_lamports: u64,
    admin_lamports: u64,
    rent_for_949: u64,
    admin_data_len: usize,
) -> Outcome {
    // Arguments are decoded before any account is looked at.
    let (flag, bps) = match read_args(payload) {
        Some(args) => args,
        None => return Outcome::Error { code: INSTRUCTION_DID_NOT_DESERIALIZE, site: "" },
    };
    if accounts.count < 1 {
        return Outcome::Error { code: ACCOUNT_NOT_ENOUGH_KEYS, site: "admin" };
    }
    if !accounts.admin_signer {
        return Outcome::Error { code: ACCOUNT_NOT_SIGNER, site: "" };
    }
    if accounts.count < 2 {
        return Outcome::Error { code: ACCOUNT_NOT_ENOUGH_KEYS, site: "global_config" };
    }
    if !accounts.config_present {
        return Outcome::Error { code: ACCOUNT_NOT_INITIALIZED, site: "" };
    }
    if !accounts.config_owner_ok {
        return Outcome::Error { code: ACCOUNT_OWNED_BY_WRONG_PROGRAM, site: "" };
    }
    let mut cfg = match read_config(config) {
        Ok(cfg) => cfg,
        Err(None) => return Outcome::InvalidAccountData,
        Err(Some(())) => return Outcome::BorshIoError,
    };
    // The system program, the event authority and the program account are
    // loaded before any `mut` / `has_one` / seeds constraint. The program
    // account's address is not checked here.
    if accounts.count < 3 {
        return Outcome::Error { code: ACCOUNT_NOT_ENOUGH_KEYS, site: "system_program" };
    }
    if !accounts.system_ok {
        return Outcome::Error { code: INVALID_PROGRAM_ID, site: "" };
    }
    if accounts.count < 4 {
        return Outcome::Error { code: ACCOUNT_NOT_ENOUGH_KEYS, site: "event_authority" };
    }
    if accounts.count < 5 {
        return Outcome::Error { code: ACCOUNT_NOT_ENOUGH_KEYS, site: "program" };
    }
    // Constraints, in the order the captured program applies them.
    if !accounts.admin_writable {
        return Outcome::Error { code: CONSTRAINT_MUT, site: "admin" };
    }
    if !accounts.config_writable {
        return Outcome::Error { code: CONSTRAINT_MUT, site: "global_config" };
    }
    if cfg.head[ADMIN..ADMIN + 32] != admin {
        return Outcome::Error { code: INVALID_ADMIN, site: "" };
    }
    if !accounts.event_authority_ok {
        return Outcome::Error { code: CONSTRAINT_SEEDS, site: "" };
    }
    // `extend_global_config`: only an account shorter than the V941 layout is
    // topped up to the rent minimum of that layout, then reallocated.
    let mut config_after = config_lamports;
    let mut admin_after = admin_lamports;
    let mut transfer = 0u64;
    if config.len() < V941 {
        transfer = rent_for_949.saturating_sub(config_lamports);
        if transfer > 0 {
            // System `Transfer` checks, in the order that program applies them.
            if admin_data_len > 0 {
                return Outcome::FromCarriesData { transfer };
            }
            if admin_lamports < transfer {
                return Outcome::InsufficientLamports { transfer };
            }
            if !accounts.admin_system_owner {
                return Outcome::ExternalAccountLamportSpend { transfer };
            }
            admin_after -= transfer;
            config_after += transfer;
        }
    }
    cfg.head[CREATOR_FEE_CONFIGURABLE] = u8::from(flag);
    cfg.head[MAX_CONFIGURABLE_CREATOR_FEE_BPS..MAX_CONFIGURABLE_CREATOR_FEE_BPS + 8]
        .copy_from_slice(&bps.to_le_bytes());
    let event = event_bytes(timestamp, admin, flag, bps);
    // `emit!` logs first. `emit_cpi!` then needs the program account.
    if !accounts.program_ok {
        return Outcome::MissingAccountAfterEvent { event, transfer };
    }
    let mut out = cfg.head;
    out.extend_from_slice(&cfg.tail);
    Outcome::Ok { config: out, event, config_lamports: config_after, admin_lamports: admin_after }
}
