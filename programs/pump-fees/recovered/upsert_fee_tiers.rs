//! Pump Fees `upsert_fee_tiers(fee_tiers, offset)`.
//!
//! A pure model of which check stops the call, the bytes the `FeeConfig`
//! account holds afterwards, and the `UpsertFeeTiersEvent` that is logged and
//! self-CPI'd. The account is read from raw bytes the way the captured program
//! reads it. The owner, signer, writable flag, PDA seeds and the
//! event-authority / program addresses arrive as booleans worked out by the
//! caller; the admin and fee-config keys arrive as 32-byte addresses.
//!
//! `FeeConfig` is one Borsh struct with three layouts, chosen by the account
//! length (discriminator included):
//! - under 2512 bytes is `InvalidAccountData`
//! - 2512..4072 reads `fee_tiers` only; `stable_fee_tiers` and `exotic_flat_fees`
//!   come back as empty / zero
//! - 4073..4096 also reads `stable_fee_tiers`
//! - 4097 and above also reads `exotic_flat_fees`
//! The exit always writes the full struct back over the front of the account
//! and leaves the tail. A short account that cannot hold that write fails
//! after the event.
//!
//! `tests/test_pump_fees_upsert_fee_tiers_captured.py` runs the same inputs on
//! `evidence/original/pump_fees/deployed.so`. Agreement there is matching
//! behaviour on those inputs, not a byte-identity claim.

/// Anchor and program error numbers.
pub const INSTRUCTION_DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_NOT_ENOUGH_KEYS: u32 = 3005;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const ACCOUNT_NOT_SIGNER: u32 = 3010;
pub const INVALID_ADMIN: u32 = 6001;
pub const NO_FEE_TIERS: u32 = 6002;
pub const TOO_MANY_FEE_TIERS: u32 = 6003;
pub const OFFSET_NOT_CONTINUOUS: u32 = 6004;
pub const FEE_TIERS_NOT_SORTED: u32 = 6005;
pub const INVALID_FEE_TOTAL: u32 = 6006;

/// `sha256("account:FeeConfig")[..8]`.
pub const CONFIG_DISCRIMINATOR: [u8; 8] = [143, 52, 146, 187, 219, 123, 76, 155];
/// `sha256("event:UpsertFeeTiersEvent")[..8]`.
pub const UPSERT_EVENT_DISCRIMINATOR: [u8; 8] = [171, 89, 169, 187, 122, 186, 33, 204];

/// Account length (discriminator included) required before a layout is read.
pub const LEGACY_LEN: usize = 2512;
pub const STABLE_LEN: usize = 4073;
pub const FULL_LEN: usize = 4097;

pub const MAX_FEE_TIERS: usize = 50;
pub const MAX_FEE_BPS: u64 = 10_000;
const TIER_LEN: usize = 40;

/// Account-level facts that need the runtime or an address comparison.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Accounts {
    /// How many account metas the instruction carries.
    pub count: usize,
    /// `admin` signed the transaction.
    pub admin_signer: bool,
    /// `fee_config` is owned by the fees program.
    pub config_owner_ok: bool,
    /// `fee_config` is passed writable.
    pub config_writable: bool,
    /// `fee_config` is `["fee_config", config_program_id]` at the stored bump.
    pub seeds_ok: bool,
    /// `event_authority` is `["__event_authority"]` of the fees program.
    pub event_authority_ok: bool,
    /// `program` is the fees program. Checked only when the self-CPI runs.
    pub program_ok: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    Error(u32),
    InvalidAccountData,
    BorshIoError,
    /// `Fees::is_valid` overflowed. The captured program aborts the instruction.
    ProgramFailedToComplete,
    /// The event was logged, then the self-CPI could not find the fees program.
    MissingAccountAfterEvent(Vec<u8>),
    /// The event was logged and self-CPI'd, then the account was too small.
    BorshIoErrorAfterEvent(Vec<u8>),
    /// Committed config bytes and the logged event.
    Ok { config: Vec<u8>, event: Vec<u8> },
}

#[derive(Clone, Copy)]
struct Tier {
    market_cap: u128,
    fees: [u8; 24],
}

struct Config {
    bump: u8,
    admin: [u8; 32],
    flat: [u8; 24],
    normal: Vec<Tier>,
    stable: Vec<Tier>,
    exotic: [u8; 24],
}

enum LoadError {
    Invalid,
    Borsh,
}

fn read_u32(buf: &mut &[u8]) -> Option<u32> {
    if buf.len() < 4 {
        return None;
    }
    let n = u32::from_le_bytes(buf[..4].try_into().unwrap());
    *buf = &buf[4..];
    Some(n)
}

fn read_tiers(buf: &mut &[u8]) -> Result<Vec<Tier>, ()> {
    let n = read_u32(buf).ok_or(())? as usize;
    let bytes = n.checked_mul(TIER_LEN).ok_or(())?;
    if buf.len() < bytes {
        return Err(());
    }
    let mut tiers = Vec::with_capacity(n);
    for chunk in buf[..bytes].chunks(TIER_LEN) {
        tiers.push(Tier {
            market_cap: u128::from_le_bytes(chunk[..16].try_into().unwrap()),
            fees: chunk[16..40].try_into().unwrap(),
        });
    }
    *buf = &buf[bytes..];
    Ok(tiers)
}

/// `None` is a short or over-long argument buffer (`InstructionDidNotDeserialize`).
/// Bytes after the offset are ignored.
fn read_args(payload: &[u8]) -> Option<(Vec<Tier>, u8)> {
    let mut buf = payload;
    let tiers = read_tiers(&mut buf).ok()?;
    let offset = *buf.first()?;
    Some((tiers, offset))
}

fn read_config(data: &[u8]) -> Result<Config, LoadError> {
    if data.len() < LEGACY_LEN || data[..8] != CONFIG_DISCRIMINATOR {
        return Err(LoadError::Invalid);
    }
    let mut rest = &data[8..];
    if rest.len() < 57 {
        return Err(LoadError::Invalid);
    }
    let bump = rest[0];
    let admin = rest[1..33].try_into().unwrap();
    let flat = rest[33..57].try_into().unwrap();
    rest = &rest[57..];
    let normal = read_tiers(&mut rest).map_err(|_| LoadError::Borsh)?;
    let stable = if data.len() >= STABLE_LEN {
        read_tiers(&mut rest).map_err(|_| LoadError::Borsh)?
    } else {
        Vec::new()
    };
    let exotic = if data.len() >= FULL_LEN {
        if rest.len() < 24 {
            return Err(LoadError::Borsh);
        }
        rest[..24].try_into().unwrap()
    } else {
        [0; 24]
    };
    Ok(Config { bump, admin, flat, normal, stable, exotic })
}

fn write_tiers(out: &mut Vec<u8>, tiers: &[Tier]) {
    out.extend_from_slice(&(tiers.len() as u32).to_le_bytes());
    for tier in tiers {
        out.extend_from_slice(&tier.market_cap.to_le_bytes());
        out.extend_from_slice(&tier.fees);
    }
}

fn serialize(config: &Config) -> Vec<u8> {
    let mut out = Vec::new();
    out.extend_from_slice(&CONFIG_DISCRIMINATOR);
    out.push(config.bump);
    out.extend_from_slice(&config.admin);
    out.extend_from_slice(&config.flat);
    write_tiers(&mut out, &config.normal);
    write_tiers(&mut out, &config.stable);
    out.extend_from_slice(&config.exotic);
    out
}

/// `(lp + protocol) + creator`, the order `Fees::is_valid` adds in.
fn fee_total(fees: &[u8; 24]) -> Option<u64> {
    let lp = u64::from_le_bytes(fees[0..8].try_into().unwrap());
    let protocol = u64::from_le_bytes(fees[8..16].try_into().unwrap());
    let creator = u64::from_le_bytes(fees[16..24].try_into().unwrap());
    lp.checked_add(protocol).and_then(|sum| sum.checked_add(creator))
}

fn event_bytes(timestamp: i64, admin: &[u8; 32], config: &[u8; 32], tiers: &[Tier], offset: u8) -> Vec<u8> {
    let mut out = Vec::new();
    out.extend_from_slice(&UPSERT_EVENT_DISCRIMINATOR);
    out.extend_from_slice(&timestamp.to_le_bytes());
    out.extend_from_slice(admin);
    out.extend_from_slice(config);
    write_tiers(&mut out, tiers);
    out.push(offset);
    out
}

pub fn upsert_fee_tiers(
    payload: &[u8],
    accounts: &Accounts,
    config: &[u8],
    admin: [u8; 32],
    fee_config: [u8; 32],
    timestamp: i64,
) -> Outcome {
    // Arguments are decoded before any account is looked at.
    let (incoming, offset) = match read_args(payload) {
        Some(args) => args,
        None => return Outcome::Error(INSTRUCTION_DID_NOT_DESERIALIZE),
    };
    // `fee_config` is loaded first: present, owner, then the layout.
    if accounts.count < 1 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if !accounts.config_owner_ok {
        return Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM);
    }
    let mut cfg = match read_config(config) {
        Ok(cfg) => cfg,
        Err(LoadError::Invalid) => return Outcome::InvalidAccountData,
        Err(LoadError::Borsh) => return Outcome::BorshIoError,
    };
    // `admin` is next. The other three metas are only checked for presence
    // until the constraints below; a missing one fails before `seeds`.
    if accounts.count < 2 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if !accounts.admin_signer {
        return Outcome::Error(ACCOUNT_NOT_SIGNER);
    }
    if accounts.count < 5 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if !accounts.seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.config_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if cfg.admin != admin {
        return Outcome::Error(INVALID_ADMIN);
    }
    if !accounts.event_authority_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }

    if incoming.is_empty() {
        return Outcome::Error(NO_FEE_TIERS);
    }
    if (offset as usize) > cfg.normal.len() {
        return Outcome::Error(OFFSET_NOT_CONTINUOUS);
    }
    let end = match (offset as usize).checked_add(incoming.len()) {
        Some(end) => end,
        None => return Outcome::Error(TOO_MANY_FEE_TIERS),
    };
    let new_len = cfg.normal.len().max(end);
    if new_len > MAX_FEE_TIERS {
        return Outcome::Error(TOO_MANY_FEE_TIERS);
    }
    let mut merged = cfg.normal.clone();
    if end > merged.len() {
        merged.resize(end, Tier { market_cap: 0, fees: [0; 24] });
    }
    merged[offset as usize..end].copy_from_slice(&incoming);
    // Every tier in the merged list, including ones the splice kept.
    for tier in &merged {
        match fee_total(&tier.fees) {
            None => return Outcome::ProgramFailedToComplete,
            Some(total) if total > MAX_FEE_BPS => return Outcome::Error(INVALID_FEE_TOTAL),
            Some(_) => {}
        }
    }
    for pair in merged.windows(2) {
        if pair[0].market_cap >= pair[1].market_cap {
            return Outcome::Error(FEE_TIERS_NOT_SORTED);
        }
    }
    cfg.normal = merged;
    let event = event_bytes(timestamp, &cfg.admin, &fee_config, &incoming, offset);
    // `emit!` logs before `emit_cpi!`. A wrong program account fails the CPI
    // and never reaches the account write.
    if !accounts.program_ok {
        return Outcome::MissingAccountAfterEvent(event);
    }
    let written = serialize(&cfg);
    if written.len() > config.len() {
        return Outcome::BorshIoErrorAfterEvent(event);
    }
    let mut out = config.to_vec();
    out[..written.len()].copy_from_slice(&written);
    Outcome::Ok { config: out, event }
}
