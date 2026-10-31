//! PumpSwap `update_fee_config`.
//!
//! A pure model of which check stops the call, the bytes the `GlobalConfig`
//! account holds afterwards, and the `UpdateFeeConfigEvent` that is logged.
//! The config is read from raw bytes the way the captured program reads it;
//! the owner, signer, writable flag and the event-authority / program
//! addresses arrive as booleans worked out by the caller.
//!
//! `tests/test_pump_amm_update_fee_config_captured.py` runs the same inputs
//! on `evidence/original/pump_amm/deployed.so`. Agreement there is matching
//! behaviour on those inputs, not a byte-identity claim.

/// Anchor and program error numbers.
pub const INSTRUCTION_DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_NOT_ENOUGH_KEYS: u32 = 3005;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const ACCOUNT_NOT_SIGNER: u32 = 3010;
pub const FEE_BASIS_POINTS_EXCEEDS_MAXIMUM: u32 = 6000;
pub const INVALID_ADMIN: u32 = 6005;
pub const ALL_PROTOCOL_FEE_RECIPIENTS_SHOULD_BE_NON_ZERO: u32 = 6011;
pub const UNSORTED_NOT_UNIQUE_PROTOCOL_FEE_RECIPIENTS: u32 = 6012;

/// `sha256("account:GlobalConfig")[..8]`.
pub const CONFIG_DISCRIMINATOR: [u8; 8] = [149, 8, 156, 202, 160, 252, 176, 217];
/// `sha256("event:UpdateFeeConfigEvent")[..8]`.
pub const UPDATE_FEE_CONFIG_EVENT_DISCRIMINATOR: [u8; 8] = [90, 23, 65, 35, 62, 244, 188, 208];

/// Account lengths (discriminator included) at which each layout is read.
/// Under `V899` the account is `InvalidAccountData`. Missing fields read as
/// zero, and the whole `V941` struct is written back.
pub const V899: usize = 907;
pub const V932: usize = 940;
pub const V941: usize = 949;

pub const ADMIN: usize = 8;
pub const LP_FEE: usize = 40;
pub const PROTOCOL_FEE: usize = 48;
pub const PROTOCOL_FEE_RECIPIENTS: usize = 57;
pub const COIN_CREATOR_FEE: usize = 313;
pub const ADMIN_SET_COIN_CREATOR_AUTHORITY: usize = 321;
pub const MAYHEM_MODE_ENABLED: usize = 417;
pub const IS_CASHBACK_ENABLED: usize = 642;
pub const BOOST_ENABLED: usize = 939;
pub const CREATOR_FEE_CONFIGURABLE: usize = 940;

/// Highest basis-point value accepted for each of the three fee fields.
pub const MAX_FEE_BASIS_POINTS: u64 = 1000;

/// Borsh size of the five arguments, before any ignored trailing bytes.
const ARG_LEN: usize = 8 + 8 + 32 * 8 + 8 + 32;

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
    /// `site` is `lp`, `protocol` or `creator` when `code` is 6000, and empty
    /// otherwise. The three fee fields share one error number; the captured
    /// program's Anchor log names the field.
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

struct Args {
    lp: u64,
    protocol: u64,
    recipients: [[u8; 32]; 8],
    creator: u64,
    authority: [u8; 32],
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

/// Five Borsh fields. A short payload does not deserialize; trailing bytes
/// are ignored.
fn read_args(payload: &[u8]) -> Option<Args> {
    if payload.len() < ARG_LEN {
        return None;
    }
    let mut recipients = [[0u8; 32]; 8];
    for (i, recipient) in recipients.iter_mut().enumerate() {
        let at = 16 + 32 * i;
        recipient.copy_from_slice(&payload[at..at + 32]);
    }
    let mut authority = [0u8; 32];
    authority.copy_from_slice(&payload[280..312]);
    Some(Args {
        lp: u64::from_le_bytes(payload[0..8].try_into().unwrap()),
        protocol: u64::from_le_bytes(payload[8..16].try_into().unwrap()),
        recipients,
        creator: u64::from_le_bytes(payload[272..280].try_into().unwrap()),
        authority,
    })
}

fn fee_site(fee: u64, site: &'static str) -> Option<Outcome> {
    if fee > MAX_FEE_BASIS_POINTS {
        Some(Outcome::Error { code: FEE_BASIS_POINTS_EXCEEDS_MAXIMUM, site })
    } else {
        None
    }
}

/// Zero keys first, then each adjacent pair strictly ascending.
fn recipient_error(recipients: &[[u8; 32]; 8]) -> Option<Outcome> {
    if recipients.iter().any(|key| *key == [0u8; 32]) {
        return Some(Outcome::Error {
            code: ALL_PROTOCOL_FEE_RECIPIENTS_SHOULD_BE_NON_ZERO,
            site: "",
        });
    }
    if recipients.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Some(Outcome::Error {
            code: UNSORTED_NOT_UNIQUE_PROTOCOL_FEE_RECIPIENTS,
            site: "",
        });
    }
    None
}

pub fn update_fee_config(
    payload: &[u8],
    accounts: &Accounts,
    config: &[u8],
    admin: [u8; 32],
    timestamp: i64,
) -> Outcome {
    // Arguments are decoded before any account is looked at.
    let args = match read_args(payload) {
        Some(args) => args,
        None => return Outcome::Error { code: INSTRUCTION_DID_NOT_DESERIALIZE, site: "" },
    };
    if accounts.count < 1 {
        return Outcome::Error { code: ACCOUNT_NOT_ENOUGH_KEYS, site: "" };
    }
    if !accounts.admin_signer {
        return Outcome::Error { code: ACCOUNT_NOT_SIGNER, site: "" };
    }
    if accounts.count < 2 {
        return Outcome::Error { code: ACCOUNT_NOT_ENOUGH_KEYS, site: "" };
    }
    if !accounts.config_owner_ok {
        return Outcome::Error { code: ACCOUNT_OWNED_BY_WRONG_PROGRAM, site: "" };
    }
    let mut cfg = match read_config(config) {
        Ok(cfg) => cfg,
        Err(None) => return Outcome::InvalidAccountData,
        Err(Some(())) => return Outcome::BorshIoError,
    };
    if accounts.count < 4 {
        return Outcome::Error { code: ACCOUNT_NOT_ENOUGH_KEYS, site: "" };
    }
    // Constraints: `mut`, `has_one = admin`, then the event-authority seeds.
    // The config address itself is not checked.
    if !accounts.config_writable {
        return Outcome::Error { code: CONSTRAINT_MUT, site: "" };
    }
    if cfg.head[ADMIN..ADMIN + 32] != admin {
        return Outcome::Error { code: INVALID_ADMIN, site: "" };
    }
    if !accounts.event_authority_ok {
        return Outcome::Error { code: CONSTRAINT_SEEDS, site: "" };
    }
    // Handler order: lp, protocol, recipients (zero, then strictly ascending), creator.
    if let Some(outcome) = fee_site(args.lp, "lp") {
        return outcome;
    }
    if let Some(outcome) = fee_site(args.protocol, "protocol") {
        return outcome;
    }
    if let Some(outcome) = recipient_error(&args.recipients) {
        return outcome;
    }
    if let Some(outcome) = fee_site(args.creator, "creator") {
        return outcome;
    }
    cfg.head[LP_FEE..LP_FEE + 8].copy_from_slice(&args.lp.to_le_bytes());
    cfg.head[PROTOCOL_FEE..PROTOCOL_FEE + 8].copy_from_slice(&args.protocol.to_le_bytes());
    for (i, recipient) in args.recipients.iter().enumerate() {
        let at = PROTOCOL_FEE_RECIPIENTS + 32 * i;
        cfg.head[at..at + 32].copy_from_slice(recipient);
    }
    cfg.head[COIN_CREATOR_FEE..COIN_CREATOR_FEE + 8].copy_from_slice(&args.creator.to_le_bytes());
    cfg.head[ADMIN_SET_COIN_CREATOR_AUTHORITY..ADMIN_SET_COIN_CREATOR_AUTHORITY + 32]
        .copy_from_slice(&args.authority);
    let mut event = Vec::with_capacity(360);
    event.extend_from_slice(&UPDATE_FEE_CONFIG_EVENT_DISCRIMINATOR);
    event.extend_from_slice(&timestamp.to_le_bytes());
    event.extend_from_slice(&admin);
    event.extend_from_slice(&args.lp.to_le_bytes());
    event.extend_from_slice(&args.protocol.to_le_bytes());
    for recipient in &args.recipients {
        event.extend_from_slice(recipient);
    }
    event.extend_from_slice(&args.creator.to_le_bytes());
    event.extend_from_slice(&args.authority);
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
