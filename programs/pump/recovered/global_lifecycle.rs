//! Captured behavior of Pump `initialize`, the three Global toggles, and
//! `update_global_authority`.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_global_lifecycle_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Attribution: SpaceXAI grok-4.7-high-fast, Cursor cloud agent.

pub const GLOBAL_LEN: usize = 1088;
pub const GLOBAL_DISC: [u8; 8] = [167, 232, 232, 177, 200, 108, 114, 127];
/// Default rent-exempt balance for 1088 bytes: `(1088 + 128) * 6960`.
pub const DEFAULT_RENT: u64 = 8_463_360;
const AUTHORITY_EVENT: [u8; 8] = [182, 195, 137, 42, 35, 206, 207, 247];

pub const OFF_CREATE_V2: usize = 450;
pub const OFF_MAYHEM: usize = 515;
pub const OFF_CASHBACK: usize = 740;

pub const IX_DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const NOT_ENOUGH_KEYS: u32 = 3005;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const NOT_SIGNER: u32 = 3010;
pub const NOT_AUTHORIZED: u32 = 6000;
/// System program `AccountAlreadyInUse`.
pub const SYSTEM_ALREADY_IN_USE: u32 = 0;
/// System program `InsufficientFunds`.
pub const SYSTEM_INSUFFICIENT: u32 = 1;

#[derive(Clone, Copy)]
pub struct InitAdmission {
    pub user_signer: bool,
    pub user_writable: bool,
    pub global_writable: bool,
    pub system_ok: bool,
    pub is_pda: bool,
    pub global_present: bool,
    pub owner_is_system: bool,
    pub system_present: bool,
    pub user_present: bool,
}

impl InitAdmission {
    pub fn from_flags(flags: u32) -> Self {
        let bit = |n: u32| flags & (1u32 << n) != 0;
        Self {
            user_signer: bit(0),
            user_writable: bit(1),
            global_writable: bit(2),
            system_ok: bit(3),
            is_pda: bit(4),
            global_present: bit(5),
            owner_is_system: bit(6),
            system_present: bit(7),
            user_present: bit(8),
        }
    }
}

pub enum Stop {
    Code(u32),
    /// System `create_account` refused a non-writable account.
    Privilege,
    /// Self-CPI target was not the Pump program. The write does not stick.
    MissingAccount,
}

pub struct Initialized {
    pub lamports: u64,
    pub data: Vec<u8>,
    /// `None` when the debit leaves the user at zero and the SVM drops it.
    pub user_lamports: Option<u64>,
}

fn blank_global(user: [u8; 32]) -> Vec<u8> {
    let mut data = vec![0u8; GLOBAL_LEN];
    data[..8].copy_from_slice(&GLOBAL_DISC);
    data[8] = 1;
    data[9..41].copy_from_slice(&user);
    data
}

/// Account checks observed before the system `create_account` CPI.
pub fn initialize(
    admission: InitAdmission,
    user_lamports: u64,
    global_lamports: u64,
    user: [u8; 32],
    global_data: &[u8],
) -> Result<Initialized, Stop> {
    if !admission.user_present {
        return Err(Stop::Code(NOT_ENOUGH_KEYS));
    }
    if !admission.user_signer {
        return Err(Stop::Code(NOT_SIGNER));
    }
    if !admission.system_present {
        return Err(Stop::Code(NOT_ENOUGH_KEYS));
    }
    if !admission.system_ok {
        return Err(Stop::Code(INVALID_PROGRAM_ID));
    }
    if !admission.is_pda {
        return Err(Stop::Code(CONSTRAINT_SEEDS));
    }
    if !admission.global_writable || !admission.user_writable {
        return Err(Stop::Privilege);
    }
    let (already, current) = if !admission.global_present {
        (false, 0)
    } else if admission.owner_is_system && global_data.is_empty() {
        (false, global_lamports)
    } else {
        (true, global_lamports)
    };
    if already {
        return Err(Stop::Code(SYSTEM_ALREADY_IN_USE));
    }
    let needed = DEFAULT_RENT.saturating_sub(current);
    if user_lamports < needed {
        return Err(Stop::Code(SYSTEM_INSUFFICIENT));
    }
    let left = user_lamports - needed;
    Ok(Initialized {
        lamports: current.max(DEFAULT_RENT),
        data: blank_global(user),
        user_lamports: if left == 0 { None } else { Some(left) },
    })
}

fn toggle_offset(name: &str) -> Option<usize> {
    match name {
        "toggle_create_v2" => Some(OFF_CREATE_V2),
        "toggle_mayhem_mode" => Some(OFF_MAYHEM),
        "toggle_cashback_enabled" => Some(OFF_CASHBACK),
        _ => None,
    }
}

/// `flags`: event present, program present, event is the PDA, authority matches,
/// authority signs, global writable, authority writable.
pub fn toggle(name: &str, flags: u32, arg: &[u8], data: &[u8]) -> Result<Vec<u8>, Stop> {
    let offset = toggle_offset(name).ok_or(Stop::Code(0))?;
    if arg.is_empty() || arg[0] > 1 {
        return Err(Stop::Code(IX_DID_NOT_DESERIALIZE));
    }
    let bit = |n: u32| flags & (1u32 << n) != 0;
    if !bit(4) {
        return Err(Stop::Code(NOT_SIGNER));
    }
    if !bit(0) || !bit(1) {
        return Err(Stop::Code(NOT_ENOUGH_KEYS));
    }
    if !bit(5) {
        return Err(Stop::Code(CONSTRAINT_MUT));
    }
    if !bit(3) {
        return Err(Stop::Code(NOT_AUTHORIZED));
    }
    if !bit(6) {
        return Err(Stop::Code(CONSTRAINT_MUT));
    }
    if !bit(2) {
        return Err(Stop::Code(CONSTRAINT_SEEDS));
    }
    if data.get(offset).copied() == Some(arg[0]) {
        return Err(Stop::Code(NOT_AUTHORIZED));
    }
    let mut next = data.to_vec();
    next[offset] = arg[0];
    Ok(next)
}

/// `flags`: event present, program present, event is the PDA, authority signs,
/// global writable, program is Pump, authority matches.
pub fn rotate_authority(
    flags: u32,
    timestamp: i64,
    global: [u8; 32],
    new_authority: [u8; 32],
    data: &[u8],
) -> Result<(Vec<u8>, Vec<u8>), Stop> {
    let bit = |n: u32| flags & (1u32 << n) != 0;
    if !bit(3) {
        return Err(Stop::Code(NOT_SIGNER));
    }
    if !bit(0) || !bit(1) {
        return Err(Stop::Code(NOT_ENOUGH_KEYS));
    }
    if !bit(4) {
        return Err(Stop::Code(CONSTRAINT_MUT));
    }
    if !bit(6) {
        return Err(Stop::Code(NOT_AUTHORIZED));
    }
    if !bit(2) {
        return Err(Stop::Code(CONSTRAINT_SEEDS));
    }
    if !bit(5) {
        return Err(Stop::MissingAccount);
    }
    let mut next = data.to_vec();
    let old = {
        let mut key = [0u8; 32];
        key.copy_from_slice(&next[9..41]);
        key
    };
    next[9..41].copy_from_slice(&new_authority);
    let mut event = Vec::with_capacity(112);
    event.extend_from_slice(&AUTHORITY_EVENT);
    event.extend_from_slice(&global);
    event.extend_from_slice(&old);
    event.extend_from_slice(&new_authority);
    event.extend_from_slice(&timestamp.to_le_bytes());
    Ok((next, event))
}
