//! Behavioral model of seven captured Pump global-admin instructions.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_global_admin_captured.py`. This file is not linked into the
//! SBF crate and does not claim byte identity with any original window.
//!
//! Attribution: SpaceXAI grok-4.7-high-fast, Cursor cloud agent.

pub const GLOBAL_LEN: usize = 1088;
pub const GLOBAL_DISC: [u8; 8] = [167, 232, 232, 177, 200, 108, 114, 127];
/// Wrapped SOL. The captured `add_quote_mint` rejects this mint; `remove_quote_mint` does not.
pub const WSOL: [u8; 32] = [
    6, 155, 136, 87, 254, 171, 129, 132, 251, 104, 127, 99, 70, 24, 192, 53, 218, 196, 57, 220, 26,
    235, 59, 85, 152, 160, 240, 0, 0, 0, 0, 1,
];
const CREATOR_FEE_EVENT: [u8; 8] = [152, 198, 124, 124, 106, 246, 127, 191];

const OFF_RECIPIENTS: usize = 741;
const OFF_BPS: usize = 997;
const OFF_RESERVES: usize = 1005;
const OFF_WHITELIST: usize = 1013;
const OFF_CONFIGURABLE: usize = 1045;
const OFF_MAX_FEE: usize = 1046;
const OFF_HOLDER_AUTH: usize = 1054;
const OFF_HOLDER_ENABLED: usize = 1086;
const OFF_DEPTH: usize = 1087;

/// Anchor and Pump custom codes observed from the captured program.
pub const IX_DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const DISC_NOT_FOUND: u32 = 3001;
pub const DISC_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const NOT_ENOUGH_KEYS: u32 = 3005;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const NOT_SIGNER: u32 = 3010;
pub const NOT_INITIALIZED: u32 = 3012;
pub const NOT_AUTHORIZED: u32 = 6000;
pub const BUYBACK_RECIPIENTS_ZERO: u32 = 6058;
pub const BUYBACK_RECIPIENTS_DUP: u32 = 6059;
pub const BUYBACK_BPS_RANGE: u32 = 6060;
pub const BUYBACK_RECIPIENTS_COUNT: u32 = 6061;
pub const WHITELIST_FULL: u32 = 6066;
pub const ALREADY_WHITELISTED: u32 = 6067;
pub const NOT_WHITELISTED: u32 = 6068;
pub const NOT_ELIGIBLE: u32 = 6069;

#[derive(Clone, Copy)]
pub struct Admission {
    pub present: bool,
    pub owner_ok: bool,
    pub is_pda: bool,
    pub global_writable: bool,
    pub authority_signer: bool,
    pub authority_matches: bool,
    pub authority_writable: bool,
    pub event_present: bool,
    pub event_is_pda: bool,
    pub program_present: bool,
    pub program_is_pump: bool,
}

impl Admission {
    pub fn from_flags(flags: u32) -> Self {
        let bit = |n: u32| flags & (1u32 << n) != 0;
        Self {
            present: bit(0),
            owner_ok: bit(1),
            is_pda: bit(2),
            global_writable: bit(3),
            authority_signer: bit(4),
            authority_matches: bit(5),
            authority_writable: bit(6),
            event_present: bit(7),
            event_is_pda: bit(8),
            program_present: bit(9),
            program_is_pump: bit(10),
        }
    }
}

#[derive(Clone, Copy)]
enum Op {
    Quote { remove: bool, mint: [u8; 32] },
    Buyback { bps: Option<u64> },
    Depth(u8),
    Reserves(u64),
    Creator { configurable: u8, max_fee: u64 },
    Holder { enabled: u8, authority: [u8; 32] },
}

pub enum Stop {
    Code(u32),
    /// `update_creator_fee_config` self-CPI did not land. The global write does not stick.
    MissingAccount,
}

pub struct Applied {
    pub data: Vec<u8>,
    pub event: Option<Vec<u8>>,
}

fn read32(data: &[u8], at: usize) -> [u8; 32] {
    data[at..at + 32].try_into().unwrap()
}

fn write32(data: &mut [u8], at: usize, key: [u8; 32]) {
    data[at..at + 32].copy_from_slice(&key);
}

fn parse(name: &str, arg: &[u8]) -> Result<Op, u32> {
    match name {
        "add_quote_mint" | "remove_quote_mint" => {
            if arg.len() < 32 {
                return Err(IX_DID_NOT_DESERIALIZE);
            }
            let mut mint = [0u8; 32];
            mint.copy_from_slice(&arg[..32]);
            Ok(Op::Quote { remove: name == "remove_quote_mint", mint })
        }
        "update_buyback_config" => {
            if arg.is_empty() {
                return Err(IX_DID_NOT_DESERIALIZE);
            }
            match arg[0] {
                0 => Ok(Op::Buyback { bps: None }),
                1 if arg.len() >= 9 => Ok(Op::Buyback {
                    bps: Some(u64::from_le_bytes(arg[1..9].try_into().unwrap())),
                }),
                1 => Err(IX_DID_NOT_DESERIALIZE),
                _ => Err(IX_DID_NOT_DESERIALIZE),
            }
        }
        "set_max_curve_depth" => {
            if arg.is_empty() {
                return Err(IX_DID_NOT_DESERIALIZE);
            }
            Ok(Op::Depth(arg[0]))
        }
        "set_virtual_quote_reserves" => {
            if arg.len() < 8 {
                return Err(IX_DID_NOT_DESERIALIZE);
            }
            Ok(Op::Reserves(u64::from_le_bytes(arg[..8].try_into().unwrap())))
        }
        "update_creator_fee_config" => {
            if arg.is_empty() || arg[0] > 1 || arg.len() < 9 {
                return Err(IX_DID_NOT_DESERIALIZE);
            }
            Ok(Op::Creator {
                configurable: arg[0],
                max_fee: u64::from_le_bytes(arg[1..9].try_into().unwrap()),
            })
        }
        "update_holder_reward_config" => {
            if arg.is_empty() || arg[0] > 1 || arg.len() < 33 {
                return Err(IX_DID_NOT_DESERIALIZE);
            }
            let mut authority = [0u8; 32];
            authority.copy_from_slice(&arg[1..33]);
            Ok(Op::Holder { enabled: arg[0], authority })
        }
        _ => Err(0),
    }
}

/// Admission order observed on the captured program when these faults are combined.
/// Instruction bytes are rejected before any account check.
fn admit(a: &Admission, data: &[u8]) -> Result<(), u32> {
    if !a.present {
        return Err(NOT_INITIALIZED);
    }
    if !a.owner_ok {
        return Err(OWNED_BY_WRONG_PROGRAM);
    }
    if data.len() < 8 {
        return Err(DISC_NOT_FOUND);
    }
    if data[..8] != GLOBAL_DISC {
        return Err(DISC_MISMATCH);
    }
    if data.len() < GLOBAL_LEN {
        return Err(DID_NOT_DESERIALIZE);
    }
    if !a.authority_signer {
        return Err(NOT_SIGNER);
    }
    if !a.event_present || !a.program_present {
        return Err(NOT_ENOUGH_KEYS);
    }
    if !a.is_pda {
        return Err(CONSTRAINT_SEEDS);
    }
    if !a.global_writable {
        return Err(CONSTRAINT_MUT);
    }
    if !a.authority_matches {
        return Err(NOT_AUTHORIZED);
    }
    if !a.authority_writable {
        return Err(CONSTRAINT_MUT);
    }
    if !a.event_is_pda {
        return Err(CONSTRAINT_SEEDS);
    }
    Ok(())
}

fn apply_op(op: Op, data: &mut [u8], remaining: &[[u8; 32]], timestamp: i64) -> Result<Option<Vec<u8>>, u32> {
    match op {
        Op::Quote { remove, mint } => {
            let slot = read32(data, OFF_WHITELIST);
            if remove {
                if mint == [0u8; 32] {
                    return Err(NOT_ELIGIBLE);
                }
                if slot != mint {
                    return Err(NOT_WHITELISTED);
                }
                write32(data, OFF_WHITELIST, [0u8; 32]);
            } else {
                if mint == [0u8; 32] || mint == WSOL {
                    return Err(NOT_ELIGIBLE);
                }
                if slot == mint {
                    return Err(ALREADY_WHITELISTED);
                }
                if slot != [0u8; 32] {
                    return Err(WHITELIST_FULL);
                }
                write32(data, OFF_WHITELIST, mint);
            }
            Ok(None)
        }
        Op::Buyback { bps } => {
            if let Some(value) = bps {
                if value > 10_000 {
                    return Err(BUYBACK_BPS_RANGE);
                }
            }
            match remaining.len() {
                0 => {}
                8 => {
                    if remaining.iter().any(|key| *key == [0u8; 32]) {
                        return Err(BUYBACK_RECIPIENTS_ZERO);
                    }
                    for left in 0..8 {
                        for right in left + 1..8 {
                            if remaining[left] == remaining[right] {
                                return Err(BUYBACK_RECIPIENTS_DUP);
                            }
                        }
                    }
                }
                _ => return Err(BUYBACK_RECIPIENTS_COUNT),
            }
            if let Some(value) = bps {
                data[OFF_BPS..OFF_BPS + 8].copy_from_slice(&value.to_le_bytes());
            }
            if remaining.len() == 8 {
                for (i, key) in remaining.iter().enumerate() {
                    write32(data, OFF_RECIPIENTS + i * 32, *key);
                }
            }
            Ok(None)
        }
        Op::Depth(depth) => {
            data[OFF_DEPTH] = depth;
            Ok(None)
        }
        Op::Reserves(value) => {
            data[OFF_RESERVES..OFF_RESERVES + 8].copy_from_slice(&value.to_le_bytes());
            Ok(None)
        }
        Op::Creator { configurable, max_fee } => {
            data[OFF_CONFIGURABLE] = configurable;
            data[OFF_MAX_FEE..OFF_MAX_FEE + 8].copy_from_slice(&max_fee.to_le_bytes());
            let mut event = Vec::with_capacity(57);
            event.extend_from_slice(&CREATOR_FEE_EVENT);
            event.extend_from_slice(&timestamp.to_le_bytes());
            event.extend_from_slice(&read32(data, 9));
            event.push(configurable);
            event.extend_from_slice(&max_fee.to_le_bytes());
            Ok(Some(event))
        }
        Op::Holder { enabled, authority } => {
            data[OFF_HOLDER_ENABLED] = enabled;
            write32(data, OFF_HOLDER_AUTH, authority);
            Ok(None)
        }
    }
}

pub fn apply(
    name: &str,
    admission: Admission,
    timestamp: i64,
    arg: &[u8],
    data: &[u8],
    remaining: &[[u8; 32]],
) -> Result<Applied, Stop> {
    let op = parse(name, arg).map_err(Stop::Code)?;
    admit(&admission, data).map_err(Stop::Code)?;
    if matches!(op, Op::Creator { .. }) && !admission.program_is_pump {
        return Err(Stop::MissingAccount);
    }
    let mut next = data.to_vec();
    let event = apply_op(op, &mut next, remaining, timestamp).map_err(Stop::Code)?;
    Ok(Applied { data: next, event })
}
