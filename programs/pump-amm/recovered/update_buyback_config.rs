//! PumpSwap `update_buyback_config(buyback_basis_points: Option<u64>)`.
//!
//! A pure model of which check stops the call and the bytes the
//! `GlobalConfig` account holds afterwards. The config is read from raw bytes
//! the way the captured program reads it; the owner, signer and writable flag
//! arrive as booleans worked out by the caller, and the remaining accounts as
//! their 32-byte keys.
//!
//! The captured instruction takes the `#[event_cpi]` accounts (`admin`,
//! `global_config`, `event_authority`, `program`) although it logs no event,
//! so the buyback recipients start at the fifth meta. The `program` meta is
//! never checked.
//! `tests/test_pump_amm_update_buyback_config_captured.py` runs the same inputs
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
pub const ALL_BUYBACK_FEE_RECIPIENTS_SHOULD_BE_NON_ZERO: u32 = 6054;
pub const NOT_UNIQUE_BUYBACK_FEE_RECIPIENTS: u32 = 6055;
pub const BUYBACK_BASIS_POINTS_OUT_OF_RANGE: u32 = 6056;
pub const WRONG_BUYBACK_FEE_RECIPIENTS_COUNT: u32 = 6057;

/// `sha256("account:GlobalConfig")[..8]`.
pub const CONFIG_DISCRIMINATOR: [u8; 8] = [149, 8, 156, 202, 160, 252, 176, 217];

/// Account lengths (discriminator included) at which each layout is read.
/// Under `V899` the account is `InvalidAccountData`; fields a layout lacks
/// read as zero, and the whole `V941` struct is written back.
pub const V899: usize = 907;
pub const V932: usize = 940;
pub const V941: usize = 949;

pub const ADMIN: usize = 8;
pub const MAYHEM_MODE_ENABLED: usize = 417;
pub const IS_CASHBACK_ENABLED: usize = 642;
pub const BUYBACK_FEE_RECIPIENTS: usize = 643;
pub const BUYBACK_BASIS_POINTS: usize = 899;
pub const BOOST_ENABLED: usize = 939;
pub const CREATOR_FEE_CONFIGURABLE: usize = 940;

/// Account-level facts that need the runtime.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Accounts {
    /// Fixed metas present (0 to 4); any further metas are `remaining`.
    pub fixed: usize,
    /// `admin` signed the transaction.
    pub admin_signer: bool,
    /// `global_config` is owned by PumpSwap.
    pub config_owner_ok: bool,
    /// `global_config` is passed writable.
    pub config_writable: bool,
    /// `event_authority` is `["__event_authority"]` of PumpSwap.
    pub event_authority_ok: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    Error(u32),
    InvalidAccountData,
    BorshIoError,
    /// The new config account bytes.
    Ok(Vec<u8>),
}

/// Borsh `Option<u64>`: tag 0 or 1, then 8 bytes for `Some`. Trailing bytes
/// are ignored. `None` is a decode failure.
fn read_args(payload: &[u8]) -> Option<Option<u64>> {
    match payload.first() {
        Some(0) => Some(None),
        Some(1) if payload.len() >= 9 => Some(Some(u64::from_le_bytes(payload[1..9].try_into().unwrap()))),
        _ => None,
    }
}

/// `Err(None)` is `InvalidAccountData`, `Err(Some(()))` a `bool` above 1.
fn read_config(data: &[u8]) -> Result<Vec<u8>, Option<()>> {
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
    Ok(head)
}

pub fn update_buyback_config(
    payload: &[u8],
    accounts: &Accounts,
    remaining: &[[u8; 32]],
    config: &[u8],
    admin: [u8; 32],
) -> Outcome {
    // Arguments are decoded before any account is looked at.
    let bps = match read_args(payload) {
        Some(a) => a,
        None => return Outcome::Error(INSTRUCTION_DID_NOT_DESERIALIZE),
    };
    if accounts.fixed < 1 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if !accounts.admin_signer {
        return Outcome::Error(ACCOUNT_NOT_SIGNER);
    }
    if accounts.fixed < 2 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if !accounts.config_owner_ok {
        return Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM);
    }
    let mut head = match read_config(config) {
        Ok(h) => h,
        Err(None) => return Outcome::InvalidAccountData,
        Err(Some(())) => return Outcome::BorshIoError,
    };
    if accounts.fixed < 4 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    // Constraints: `mut`, `has_one = admin`, then the event-authority seeds.
    // The config and program addresses are not checked.
    if !accounts.config_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if head[ADMIN..ADMIN + 32] != admin {
        return Outcome::Error(INVALID_ADMIN);
    }
    if !accounts.event_authority_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    // Handler: the basis points first, then the recipients (none or exactly eight).
    if let Some(bps) = bps {
        if bps > 10_000 {
            return Outcome::Error(BUYBACK_BASIS_POINTS_OUT_OF_RANGE);
        }
        head[BUYBACK_BASIS_POINTS..BUYBACK_BASIS_POINTS + 8].copy_from_slice(&bps.to_le_bytes());
    }
    match remaining.len() {
        0 => {}
        8 => {
            if remaining.iter().any(|r| *r == [0u8; 32]) {
                return Outcome::Error(ALL_BUYBACK_FEE_RECIPIENTS_SHOULD_BE_NON_ZERO);
            }
            for i in 0..8 {
                for j in i + 1..8 {
                    if remaining[i] == remaining[j] {
                        return Outcome::Error(NOT_UNIQUE_BUYBACK_FEE_RECIPIENTS);
                    }
                }
            }
            for (i, r) in remaining.iter().enumerate() {
                let at = BUYBACK_FEE_RECIPIENTS + 32 * i;
                head[at..at + 32].copy_from_slice(r);
            }
        }
        _ => return Outcome::Error(WRONG_BUYBACK_FEE_RECIPIENTS_COUNT),
    }
    // Exit writes the whole V941 struct, so an older, shorter account fails.
    if config.len() < V941 {
        return Outcome::BorshIoError;
    }
    head.extend_from_slice(&config[V941..]);
    Outcome::Ok(head)
}
