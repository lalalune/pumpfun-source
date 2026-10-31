//! PumpSwap `create_config`.
//!
//! A pure model of which check stops the call, the bytes and lamports of the
//! new `GlobalConfig`, and the `CreateConfigEvent` that is logged. The signer
//! and writable bits are the ones the runtime presents. The config address,
//! the system program, the event authority and the program id arrive as
//! booleans. The preexisting config (lamports, data length, whether it is
//! system-owned) and the rent-exemption minimum for 949 bytes are numbers
//! supplied by the caller.
//!
//! `tests/test_pump_amm_create_config_captured.py` runs the same inputs on
//! `evidence/original/pump_amm/deployed.so`. Agreement there is matching
//! behaviour on those inputs, not a byte-identity claim.

/// Anchor and program error numbers. `0` and `1` are the system program's
/// `AccountAlreadyInUse` and `InsufficientFunds`, bubbled up unchanged.
pub const INSTRUCTION_DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_NOT_ENOUGH_KEYS: u32 = 3005;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const ACCOUNT_NOT_SIGNER: u32 = 3010;
pub const FEE_BASIS_POINTS_EXCEEDS_MAXIMUM: u32 = 6000;
pub const INVALID_ADMIN: u32 = 6005;
pub const ALL_PROTOCOL_FEE_RECIPIENTS_SHOULD_BE_NON_ZERO: u32 = 6011;
pub const UNSORTED_NOT_UNIQUE_PROTOCOL_FEE_RECIPIENTS: u32 = 6012;
pub const ACCOUNT_ALREADY_IN_USE: u32 = 0;
pub const INSUFFICIENT_FUNDS: u32 = 1;

/// `sha256("account:GlobalConfig")[..8]`.
pub const CONFIG_DISCRIMINATOR: [u8; 8] = [149, 8, 156, 202, 160, 252, 176, 217];
/// `sha256("event:CreateConfigEvent")[..8]`.
pub const CREATE_CONFIG_EVENT_DISCRIMINATOR: [u8; 8] = [107, 52, 89, 129, 55, 226, 81, 22];

/// `8LWu7QM2dGR1G8nKDHthckea57bkCzXyBTAKPJUBDHo8`.
pub const FIXED_ADMIN: [u8; 32] = [
    0x6d, 0x01, 0xa6, 0x70, 0x14, 0x5f, 0x09, 0x62, 0x8d, 0xa1, 0x33, 0x91, 0x66, 0x95, 0x19, 0x1c,
    0x72, 0x6c, 0xe9, 0x4c, 0xf4, 0xed, 0xfd, 0x53, 0x5e, 0x54, 0x1e, 0x6a, 0xd7, 0xa6, 0x06, 0x53,
];

/// Bytes the instruction writes. `space = 949` in the account constraint.
pub const CONFIG_LEN: usize = 949;
pub const ADMIN: usize = 8;
pub const LP_FEE: usize = 40;
pub const PROTOCOL_FEE: usize = 48;
pub const DISABLE_FLAGS: usize = 56;
pub const PROTOCOL_FEE_RECIPIENTS: usize = 57;
pub const COIN_CREATOR_FEE: usize = 313;
pub const ADMIN_SET_COIN_CREATOR_AUTHORITY: usize = 321;

/// Highest basis-point value accepted for each of the three fee fields.
pub const MAX_FEE_BASIS_POINTS: u64 = 1000;

/// Borsh size of the five arguments, before any ignored trailing bytes.
const ARG_LEN: usize = 8 + 8 + 32 * 8 + 8 + 32;

/// Account-level facts that need the runtime or an address comparison.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Accounts {
    /// How many account metas the instruction carries.
    pub count: usize,
    /// `admin` signed, as the runtime presents it. The fee payer counts.
    pub admin_signer: bool,
    /// `admin` is writable, as the runtime presents it. The fee payer counts.
    pub admin_writable: bool,
    /// `global_config` is writable.
    pub config_writable: bool,
    /// `global_config` is the `["global_config"]` PDA.
    pub config_seeds_ok: bool,
    /// `system_program` is the system program.
    pub system_program_ok: bool,
    /// `event_authority` is `["__event_authority"]`.
    pub event_authority_ok: bool,
    /// `program` is PumpSwap itself.
    pub program_ok: bool,
    /// Lamports already on the config account. Zero means it does not exist:
    /// a zero-lamport account is created from scratch, whatever it held.
    pub config_lamports: u64,
    /// Data length of the config account. Ignored when `config_lamports` is 0.
    pub config_data_len: usize,
    /// Config is owned by the system program. Ignored when its lamports are 0.
    pub config_system_owned: bool,
    /// Lamports on `admin` before the call.
    pub admin_lamports: u64,
    /// Rent-exemption minimum for [`CONFIG_LEN`] bytes.
    pub rent: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    /// `site` names the fee field for 6000, the missing account for 3005, and
    /// the blamed account for 2006, 2000, 3010, 3008 and 6005. Empty otherwise.
    Error { code: u32, site: &'static str },
    /// The system CPI was rejected before the system program ran.
    PrivilegeEscalation,
    /// `emit!` logged the event, then `emit_cpi!` found no PumpSwap account.
    MissingAccountAfterEvent(Vec<u8>),
    /// Committed config bytes, logged event, config lamports, admin lamports.
    /// The transaction fee is not included in `admin_lamports`.
    Created {
        config: Vec<u8>,
        event: Vec<u8>,
        config_lamports: u64,
        admin_lamports: u64,
    },
}

struct Args {
    lp: u64,
    protocol: u64,
    recipients: [[u8; 32]; 8],
    creator: u64,
    authority: [u8; 32],
}

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

fn err(code: u32, site: &'static str) -> Outcome {
    Outcome::Error { code, site }
}

/// Create the config account, or the system error that stops it.
///
/// A missing account is created with `CreateAccount`. An account that already
/// holds lamports is topped up when it is short of `rent`, then `Allocate`d
/// and `Assign`ed. `Allocate` fails unless the account is empty and
/// system-owned. Debiting a non-writable admin is rejected by the runtime.
/// Once allocate and assign have succeeded, a non-writable admin is
/// `ConstraintMut`.
fn init(accounts: &Accounts) -> Result<(u64, u64), Outcome> {
    if !accounts.config_writable {
        return Err(Outcome::PrivilegeEscalation);
    }
    if accounts.config_lamports == 0 {
        if !accounts.admin_writable {
            return Err(Outcome::PrivilegeEscalation);
        }
        if accounts.admin_lamports < accounts.rent {
            return Err(err(INSUFFICIENT_FUNDS, ""));
        }
        return Ok((accounts.rent, accounts.admin_lamports - accounts.rent));
    }
    let mut admin_after = accounts.admin_lamports;
    if accounts.config_lamports < accounts.rent {
        let need = accounts.rent - accounts.config_lamports;
        if !accounts.admin_writable {
            return Err(Outcome::PrivilegeEscalation);
        }
        if accounts.admin_lamports < need {
            return Err(err(INSUFFICIENT_FUNDS, ""));
        }
        admin_after -= need;
    }
    if accounts.config_data_len > 0 || !accounts.config_system_owned {
        return Err(err(ACCOUNT_ALREADY_IN_USE, ""));
    }
    if !accounts.admin_writable {
        return Err(err(CONSTRAINT_MUT, "admin"));
    }
    let config_after = accounts.rent.max(accounts.config_lamports);
    Ok((config_after, admin_after))
}

fn event_bytes(args: &Args, admin: [u8; 32], timestamp: i64) -> Vec<u8> {
    let mut event = Vec::with_capacity(360);
    event.extend_from_slice(&CREATE_CONFIG_EVENT_DISCRIMINATOR);
    event.extend_from_slice(&timestamp.to_le_bytes());
    event.extend_from_slice(&admin);
    event.extend_from_slice(&args.lp.to_le_bytes());
    event.extend_from_slice(&args.protocol.to_le_bytes());
    for recipient in &args.recipients {
        event.extend_from_slice(recipient);
    }
    event.extend_from_slice(&args.creator.to_le_bytes());
    event.extend_from_slice(&args.authority);
    event
}

fn config_bytes(args: &Args, admin: [u8; 32]) -> Vec<u8> {
    let mut config = vec![0u8; CONFIG_LEN];
    config[..8].copy_from_slice(&CONFIG_DISCRIMINATOR);
    config[ADMIN..ADMIN + 32].copy_from_slice(&admin);
    config[LP_FEE..LP_FEE + 8].copy_from_slice(&args.lp.to_le_bytes());
    config[PROTOCOL_FEE..PROTOCOL_FEE + 8].copy_from_slice(&args.protocol.to_le_bytes());
    config[DISABLE_FLAGS] = 0;
    for (i, recipient) in args.recipients.iter().enumerate() {
        let at = PROTOCOL_FEE_RECIPIENTS + 32 * i;
        config[at..at + 32].copy_from_slice(recipient);
    }
    config[COIN_CREATOR_FEE..COIN_CREATOR_FEE + 8].copy_from_slice(&args.creator.to_le_bytes());
    config[ADMIN_SET_COIN_CREATOR_AUTHORITY..ADMIN_SET_COIN_CREATOR_AUTHORITY + 32]
        .copy_from_slice(&args.authority);
    config
}

pub fn create_config(payload: &[u8], accounts: &Accounts, admin: [u8; 32], timestamp: i64) -> Outcome {
    // Arguments are decoded before any account is looked at.
    let args = match read_args(payload) {
        Some(args) => args,
        None => return err(INSTRUCTION_DID_NOT_DESERIALIZE, ""),
    };
    // Signer is checked as soon as `admin` is present. The system-program id is
    // checked as soon as that account is present. The PDA is checked only once
    // all five accounts have been supplied.
    if accounts.count < 1 {
        return err(ACCOUNT_NOT_ENOUGH_KEYS, "admin");
    }
    if !accounts.admin_signer {
        return err(ACCOUNT_NOT_SIGNER, "admin");
    }
    if accounts.count < 2 {
        return err(ACCOUNT_NOT_ENOUGH_KEYS, "");
    }
    if accounts.count < 3 {
        return err(ACCOUNT_NOT_ENOUGH_KEYS, "system_program");
    }
    if !accounts.system_program_ok {
        return err(INVALID_PROGRAM_ID, "system_program");
    }
    if accounts.count < 4 {
        return err(ACCOUNT_NOT_ENOUGH_KEYS, "event_authority");
    }
    if accounts.count < 5 {
        return err(ACCOUNT_NOT_ENOUGH_KEYS, "program");
    }
    if !accounts.config_seeds_ok {
        return err(CONSTRAINT_SEEDS, "global_config");
    }
    // Init runs before the admin address constraint and the event-authority seeds.
    let (config_lamports, admin_lamports) = match init(accounts) {
        Ok(pair) => pair,
        Err(outcome) => return outcome,
    };
    if admin != FIXED_ADMIN {
        return err(INVALID_ADMIN, "admin");
    }
    if !accounts.event_authority_ok {
        return err(CONSTRAINT_SEEDS, "event_authority");
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
    let event = event_bytes(&args, admin, timestamp);
    if !accounts.program_ok {
        return Outcome::MissingAccountAfterEvent(event);
    }
    Outcome::Created {
        config: config_bytes(&args, admin),
        event,
        config_lamports,
        admin_lamports,
    }
}
