//! Captured behavior of Pump `admin_cto`.
//!
//! A pure model of which check stops the call, the bonding-curve bytes written
//! back, the `AdminCtoEvent`, and the lamports moved onto the curve for rent.
//! Account addresses, owners, and signer bits arrive as facts the caller
//! worked out; the curve and the global account are the raw bytes the program
//! reads.
//!
//! `tests/test_admin_cto_captured.py` runs the same inputs on
//! `evidence/original/pump/deployed.so` (with the captured Pump Fees and
//! PumpSwap programs for the two conditional CPIs). Agreement there is
//! matching behaviour on those inputs, not a byte-identity claim.
//!
//! Out of scope, and not represented here: a creator-vault balance above
//! rent, a frozen quote-token account, and a Pump Fees sharing-config body
//! the fees program rejects. Those paths move tokens or fail inside the other
//! program. The tested inputs leave the swept amount at 0.

pub const INSTRUCTION_DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const CONSTRAINT_MINT_TOKEN_PROGRAM: u32 = 2022;
pub const ACCOUNT_DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const ACCOUNT_DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const ACCOUNT_DID_NOT_DESERIALIZE: u32 = 3003;
pub const ACCOUNT_NOT_ENOUGH_KEYS: u32 = 3005;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const ACCOUNT_NOT_SIGNER: u32 = 3010;
pub const SYSTEM_INSUFFICIENT_FUNDS: u32 = 1;

pub const NOT_AUTHORIZED: u32 = 6000;
pub const INVALID_CREATOR: u32 = 6019;
pub const OVERFLOW: u32 = 6024;
pub const CREATOR_SHOULD_NOT_BE_ZERO: u32 = 6030;
pub const CREATOR_FEE_NOT_CONFIGURABLE: u32 = 6077;
pub const CREATOR_FEE_BPS_OUT_OF_RANGE: u32 = 6078;
pub const CREATOR_FEE_NOT_ALLOWED_FOR_CASHBACK: u32 = 6080;
pub const HOLDER_REWARD_CREATOR_IMMUTABLE: u32 = 6083;
pub const HOLDER_REWARD_DISABLED: u32 = 6084;
pub const CTO_NOT_ALLOWED_FOR_MAYHEM: u32 = 6088;
pub const CTO_NEW_CREATOR_REQUIRED: u32 = 6089;
pub const CTO_NEW_CREATOR_NOT_ALLOWED: u32 = 6090;
pub const CREATOR_FEE_NOT_CONFIGURABLE_FOR_QUOTE: u32 = 6091;
pub const CTO_CREATOR_ACCOUNT_NOT_WRITABLE: u32 = 6092;
pub const MINT_DOES_NOT_MATCH: u32 = 6004;
pub const CREATOR_FEES_NOT_SWEPT: u32 = 6095;

pub const CURVE_DISC: [u8; 8] = [23, 183, 248, 55, 96, 216, 172, 96];
pub const GLOBAL_DISC: [u8; 8] = [167, 232, 232, 177, 200, 108, 114, 127];
pub const EVENT_DISC: [u8; 8] = [110, 124, 226, 98, 170, 255, 17, 120];
/// Wrapped SOL. A curve whose quote mint is absent or this mint cannot take a
/// configured creator fee.
pub const WSOL: [u8; 32] = [
    6, 155, 136, 87, 254, 171, 129, 132, 251, 104, 127, 99, 70, 24, 192, 53, 218, 196, 57, 220, 26,
    235, 59, 85, 152, 160, 240, 0, 0, 0, 0, 1,
];

pub const GLOBAL_LEN: usize = 1088;
pub const CURVE_MIN: usize = 49;
pub const CURVE_WRITE: usize = 166;
pub const LAMPORTS_PER_BYTE: u64 = 6_960;

const OFF_REAL_QUOTE: usize = 32;
const OFF_CREATOR: usize = 49;
const OFF_MAYHEM: usize = 81;
const OFF_CASHBACK: usize = 82;
const OFF_QUOTE: usize = 83;
const OFF_FEE_BPS: usize = 115;
const OFF_CAN_EDIT: usize = 123;
const OFF_HOLDER: usize = 124;
const OFF_CREATOR_FEE: usize = 125;
const OFF_PROTOCOL_FEE: usize = 133;
const OFF_ADMIN: usize = 418;
const OFF_WHITELIST: usize = 1013;
const OFF_CONFIGURABLE: usize = 1045;
const OFF_MAX_FEE: usize = 1046;
const OFF_HOLDER_ENABLED: usize = 1086;
const GLOBAL_BOOLS: [usize; 7] = [8, 145, 450, 515, 740, 1045, 1086];
const CURVE_BOOLS: [usize; 5] = [48, 81, 82, 123, 124];

pub type Key = [u8; 32];

/// Facts that depend on the runtime rather than on account bytes.
#[derive(Clone, Copy)]
pub struct Accounts {
    /// How many of the 26 fixed metas were supplied, in IDL order.
    pub present: u8,
    pub admin_signer: bool,
    pub admin_writable: bool,
    pub global_owner_ok: bool,
    pub global_seeds_ok: bool,
    pub quote_owner_token_family: bool,
    pub token_program_interface: bool,
    pub quote_owner_matches_token_program: bool,
    pub ata_program_ok: bool,
    pub system_program_ok: bool,
    pub curve_owner_ok: bool,
    pub curve_seeds_ok: bool,
    pub curve_writable: bool,
    pub creator_ata_ok: bool,
    pub creator_ata_writable: bool,
    pub vault_seeds_ok: bool,
    pub vault_writable: bool,
    pub vault_ata_ok: bool,
    pub vault_ata_writable: bool,
    pub holder_vault_writable: bool,
    /// `holder_creator_vault` is the creator-vault PDA of the holder-rewards key.
    /// Checked only when the holder sweep runs.
    pub holder_vault_is_dest: bool,
    pub holder_ata_ok: bool,
    pub holder_ata_writable: bool,
    pub amm_program_ok: bool,
    pub amm_config_seeds_ok: bool,
    pub pool_auth_seeds_ok: bool,
    pub pool_seeds_ok: bool,
    pub pool_writable: bool,
    pub amm_event_ok: bool,
    pub coin_auth_seeds_ok: bool,
    pub coin_auth_writable: bool,
    pub coin_ata_ok: bool,
    pub coin_ata_writable: bool,
    pub sharing_seeds_ok: bool,
    pub sharing_writable: bool,
    pub fees_program_ok: bool,
    pub fees_event_ok: bool,
    pub event_seeds_ok: bool,
    pub program_is_pump: bool,
    pub creator_executable: bool,
    pub creator_system_owner: bool,
    pub creator_writable: bool,
    pub sharing_owner_fees: bool,
    pub sharing_nonempty: bool,
    pub pool_owner_amm: bool,
    pub pool_nonempty: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    Error(u32),
    InvalidAccountData,
    BorshIoError,
    MissingAccount,
    /// Curve bytes, the 204-byte `AdminCtoEvent`, and lamports added to the curve.
    Ok { curve: Vec<u8>, event: Vec<u8>, rent: u64 },
}

pub struct Input<'a> {
    pub payload: &'a [u8],
    pub curve: &'a [u8],
    pub global: &'a [u8],
    pub accounts: &'a Accounts,
    pub admin: Key,
    pub quote: Key,
    pub current: Key,
    pub mint: Key,
    pub curve_key: Key,
    pub sharing: Key,
    pub holder: Key,
    pub curve_lamports: u64,
    pub admin_lamports: u64,
    pub timestamp: i64,
}

fn read_u64(data: &[u8], at: usize) -> u64 {
    let mut buf = [0u8; 8];
    for i in 0..8 {
        if let Some(byte) = data.get(at + i) {
            buf[i] = *byte;
        }
    }
    u64::from_le_bytes(buf)
}

fn read_key(data: &[u8], at: usize) -> Key {
    let mut buf = [0u8; 32];
    for i in 0..32 {
        if let Some(byte) = data.get(at + i) {
            buf[i] = *byte;
        }
    }
    buf
}

/// `Option<T>` with a one-byte tag. `Some` consumes `width` further bytes.
/// A tag above 1, or a short `Some`, does not deserialize.
fn read_option<'a>(data: &'a [u8], at: &mut usize, width: usize) -> Option<Option<&'a [u8]>> {
    let tag = *data.get(*at)?;
    *at += 1;
    match tag {
        0 => Some(None),
        1 => {
            let end = at.checked_add(width)?;
            let body = data.get(*at..end)?;
            *at = end;
            Some(Some(body))
        }
        _ => None,
    }
}

fn decode(payload: &[u8]) -> Option<(bool, Option<u64>, Option<Key>)> {
    let mut at = 0;
    let holder = match read_option(payload, &mut at, 1)? {
        None => false,
        Some(body) => match body[0] {
            0 => false,
            1 => true,
            _ => return None,
        },
    };
    let fee = match read_option(payload, &mut at, 8)? {
        None => None,
        Some(body) => Some(u64::from_le_bytes(body.try_into().ok()?)),
    };
    let new_creator = match read_option(payload, &mut at, 32)? {
        None => None,
        Some(body) => Some(body.try_into().ok()?),
    };
    Some((holder, fee, new_creator))
}

fn need(accounts: &Accounts, index: u8) -> Option<Outcome> {
    if accounts.present <= index {
        Some(Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS))
    } else {
        None
    }
}

fn global_ok(global: &[u8]) -> Option<Outcome> {
    if global.len() < 8 {
        return Some(Outcome::Error(ACCOUNT_DISCRIMINATOR_NOT_FOUND));
    }
    if global[..8] != GLOBAL_DISC {
        return Some(Outcome::Error(ACCOUNT_DISCRIMINATOR_MISMATCH));
    }
    if global.len() < GLOBAL_LEN || GLOBAL_BOOLS.iter().any(|&at| global[at] > 1) {
        return Some(Outcome::Error(ACCOUNT_DID_NOT_DESERIALIZE));
    }
    None
}

fn curve_header(curve: &[u8]) -> Option<Outcome> {
    if curve.len() < CURVE_MIN || curve[..8] != CURVE_DISC {
        return Some(Outcome::InvalidAccountData);
    }
    if CURVE_BOOLS.iter().any(|&at| at < curve.len() && curve[at] > 1) {
        return Some(Outcome::BorshIoError);
    }
    None
}

fn quote_matches(curve: &[u8], quote: Key) -> bool {
    let stored = read_key(curve, OFF_QUOTE);
    stored == quote || (stored == [0u8; 32] && quote == WSOL)
}

/// Lamports the payer must add so the curve meets the rent of its written size.
/// `Err` is overflow of the reserved-fee sum, which only exists for a curve
/// whose stored quote mint is the all-zero key.
fn rent_due(curve: &[u8], lamports: u64) -> Result<u64, ()> {
    let size = (curve.len().max(CURVE_WRITE)) as u64;
    let minimum = (128 + size) * LAMPORTS_PER_BYTE;
    let reserved = if read_key(curve, OFF_QUOTE) == [0u8; 32] {
        let fees = read_u64(curve, OFF_CREATOR_FEE)
            .checked_add(read_u64(curve, OFF_PROTOCOL_FEE))
            .ok_or(())?;
        read_u64(curve, OFF_REAL_QUOTE).checked_add(fees).ok_or(())?
    } else {
        0
    };
    let available = lamports.saturating_sub(reserved);
    Ok(minimum.saturating_sub(available))
}

fn event(
    timestamp: i64,
    admin: Key,
    mint: Key,
    curve_key: Key,
    old_creator: Key,
    new_creator: Key,
    holder: bool,
    cashback: bool,
    old_fee: u64,
    new_fee: u64,
    sharing_reset: bool,
    pool_updated: bool,
) -> Vec<u8> {
    let mut out = Vec::with_capacity(204);
    out.extend_from_slice(&EVENT_DISC);
    out.extend_from_slice(&timestamp.to_le_bytes());
    out.extend_from_slice(&admin);
    out.extend_from_slice(&mint);
    out.extend_from_slice(&curve_key);
    out.extend_from_slice(&old_creator);
    out.extend_from_slice(&new_creator);
    out.push(u8::from(holder));
    out.push(u8::from(cashback));
    out.extend_from_slice(&old_fee.to_le_bytes());
    out.extend_from_slice(&new_fee.to_le_bytes());
    out.push(u8::from(sharing_reset));
    out.extend_from_slice(&0u64.to_le_bytes());
    out.push(u8::from(pool_updated));
    out
}

pub fn admin_cto(input: &Input) -> Outcome {
    let (holder, fee, new_creator) = match decode(input.payload) {
        Some(decoded) => decoded,
        None => return Outcome::Error(INSTRUCTION_DID_NOT_DESERIALIZE),
    };
    let accounts = input.accounts;

    // Accounts, in IDL order. A missing meta fails as that account is reached.
    if let Some(stop) = need(accounts, 0) {
        return stop;
    }
    if !accounts.admin_signer {
        return Outcome::Error(ACCOUNT_NOT_SIGNER);
    }
    if !accounts.admin_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if let Some(stop) = need(accounts, 1) {
        return stop;
    }
    if !accounts.global_owner_ok {
        return Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM);
    }
    if let Some(stop) = global_ok(input.global) {
        return stop;
    }
    if !accounts.global_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    // `has_one = admin_set_creator_authority` is after the seeds constraint.
    if input.global[OFF_ADMIN..OFF_ADMIN + 32] != input.admin {
        return Outcome::Error(NOT_AUTHORIZED);
    }
    if let Some(stop) = need(accounts, 2) {
        return stop;
    }
    if let Some(stop) = need(accounts, 3) {
        return stop;
    }
    if !accounts.quote_owner_token_family {
        return Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM);
    }
    // `mint::token_program` names the next account, so a missing program fails
    // here, before the quote-key constraint.
    if let Some(stop) = need(accounts, 4) {
        return stop;
    }
    if !accounts.token_program_interface {
        return Outcome::Error(INVALID_PROGRAM_ID);
    }
    if !accounts.quote_owner_matches_token_program {
        return Outcome::Error(CONSTRAINT_MINT_TOKEN_PROGRAM);
    }
    // The quote constraint reads the curve's quote mint. Under 49 bytes the
    // curve cannot be loaded (`InvalidAccountData` on `bonding_curve`), before
    // the key compare and before the curve account's owner check. A longer
    // curve is compared from its bytes; a bad discriminator is still the curve
    // account's own check, which runs after `quote_mint`.
    if input.curve.len() < CURVE_MIN {
        return Outcome::InvalidAccountData;
    }
    if !quote_matches(input.curve, input.quote) {
        return Outcome::Error(MINT_DOES_NOT_MATCH);
    }
    if let Some(stop) = need(accounts, 5) {
        return stop;
    }
    if !accounts.ata_program_ok {
        return Outcome::Error(INVALID_PROGRAM_ID);
    }
    if let Some(stop) = need(accounts, 6) {
        return stop;
    }
    if !accounts.system_program_ok {
        return Outcome::Error(INVALID_PROGRAM_ID);
    }
    if let Some(stop) = need(accounts, 7) {
        return stop;
    }
    if !accounts.curve_owner_ok {
        return Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM);
    }
    if let Some(stop) = curve_header(input.curve) {
        return stop;
    }
    // Seeds, then `mut`. A curve at the wrong address that is also read-only fails the seeds.
    if !accounts.curve_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.curve_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if let Some(stop) = need(accounts, 8) {
        return stop;
    }
    let old_creator = read_key(input.curve, OFF_CREATOR);
    if old_creator != input.current {
        return Outcome::Error(INVALID_CREATOR);
    }
    if let Some(stop) = need(accounts, 9) {
        return stop;
    }
    if !accounts.creator_ata_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.creator_ata_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if let Some(stop) = need(accounts, 10) {
        return stop;
    }
    if !accounts.vault_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.vault_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if let Some(stop) = need(accounts, 11) {
        return stop;
    }
    if !accounts.vault_ata_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.vault_ata_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if let Some(stop) = need(accounts, 12) {
        return stop;
    }
    if !accounts.holder_vault_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if let Some(stop) = need(accounts, 13) {
        return stop;
    }
    if !accounts.holder_ata_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.holder_ata_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if let Some(stop) = need(accounts, 14) {
        return stop;
    }
    if !accounts.amm_program_ok {
        return Outcome::Error(INVALID_PROGRAM_ID);
    }
    if let Some(stop) = need(accounts, 15) {
        return stop;
    }
    if !accounts.amm_config_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if let Some(stop) = need(accounts, 16) {
        return stop;
    }
    if !accounts.pool_auth_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if let Some(stop) = need(accounts, 17) {
        return stop;
    }
    if !accounts.pool_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.pool_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if let Some(stop) = need(accounts, 18) {
        return stop;
    }
    if !accounts.amm_event_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if let Some(stop) = need(accounts, 19) {
        return stop;
    }
    if !accounts.coin_auth_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.coin_auth_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if let Some(stop) = need(accounts, 20) {
        return stop;
    }
    if !accounts.coin_ata_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.coin_ata_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if let Some(stop) = need(accounts, 21) {
        return stop;
    }
    if !accounts.sharing_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.sharing_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if let Some(stop) = need(accounts, 22) {
        return stop;
    }
    if !accounts.fees_program_ok {
        return Outcome::Error(INVALID_PROGRAM_ID);
    }
    if let Some(stop) = need(accounts, 23) {
        return stop;
    }
    if !accounts.fees_event_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if let Some(stop) = need(accounts, 24) {
        return stop;
    }
    if !accounts.event_seeds_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if let Some(stop) = need(accounts, 25) {
        return stop;
    }

    // Handler. Mayhem, then the holder-reward gates, then the new creator, then
    // the fee. Account constraints have already passed.
    let mayhem = input.curve.len() > OFF_MAYHEM && input.curve[OFF_MAYHEM] == 1;
    let was_holder = input.curve.len() > OFF_HOLDER && input.curve[OFF_HOLDER] == 1;
    let was_cashback = input.curve.len() > OFF_CASHBACK && input.curve[OFF_CASHBACK] == 1;
    if mayhem {
        return Outcome::Error(CTO_NOT_ALLOWED_FOR_MAYHEM);
    }
    if was_holder && !holder {
        return Outcome::Error(HOLDER_REWARD_CREATOR_IMMUTABLE);
    }
    if holder && !was_holder && input.global[OFF_HOLDER_ENABLED] != 1 {
        return Outcome::Error(HOLDER_REWARD_DISABLED);
    }
    let target = if holder {
        if new_creator.is_some() {
            return Outcome::Error(CTO_NEW_CREATOR_NOT_ALLOWED);
        }
        input.holder
    } else {
        let Some(creator) = new_creator else {
            return Outcome::Error(CTO_NEW_CREATOR_REQUIRED);
        };
        if creator == [0u8; 32] {
            return Outcome::Error(CREATOR_SHOULD_NOT_BE_ZERO);
        }
        if creator == input.sharing || creator == input.holder {
            return Outcome::Error(INVALID_CREATOR);
        }
        creator
    };
    let cashback = !holder && was_cashback;
    if let Some(bps) = fee {
        let stored_quote = read_key(input.curve, OFF_QUOTE);
        let locked = stored_quote == [0u8; 32]
            || stored_quote == WSOL
            || stored_quote == read_key(input.global, OFF_WHITELIST);
        if locked {
            return Outcome::Error(CREATOR_FEE_NOT_CONFIGURABLE_FOR_QUOTE);
        }
        if cashback {
            return Outcome::Error(CREATOR_FEE_NOT_ALLOWED_FOR_CASHBACK);
        }
        if input.global[OFF_CONFIGURABLE] != 1 {
            return Outcome::Error(CREATOR_FEE_NOT_CONFIGURABLE);
        }
        let max_fee = read_u64(input.global, OFF_MAX_FEE);
        if bps == 0 || bps > max_fee {
            return Outcome::Error(CREATOR_FEE_BPS_OUT_OF_RANGE);
        }
    }

    let shared = old_creator == input.sharing && accounts.sharing_owner_fees && accounts.sharing_nonempty;
    let (target, sharing_reset) = if shared {
        if holder {
            (input.holder, true)
        } else {
            (old_creator, true)
        }
    } else {
        (target, false)
    };

    let due = match rent_due(input.curve, input.curve_lamports) {
        Ok(due) => due,
        Err(()) => return Outcome::Error(OVERFLOW),
    };
    if due > input.admin_lamports {
        return Outcome::Error(SYSTEM_INSUFFICIENT_FUNDS);
    }
    let creator_fee = read_u64(input.curve, OFF_CREATOR_FEE);
    if creator_fee != 0 {
        return Outcome::Error(CREATOR_FEES_NOT_SWEPT);
    }
    let collect_old = !shared && !was_holder && old_creator != [0u8; 32];
    if collect_old && !accounts.creator_executable && accounts.creator_system_owner && !accounts.creator_writable {
        return Outcome::Error(CTO_CREATOR_ACCOUNT_NOT_WRITABLE);
    }
    if shared && holder && !accounts.holder_vault_is_dest {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }

    // The program account is not checked until the event self-CPI.
    if !accounts.program_is_pump {
        return Outcome::MissingAccount;
    }

    let mut written = input.curve.to_vec();
    if written.len() < CURVE_WRITE {
        written.resize(CURVE_WRITE, 0);
    }
    written[OFF_CREATOR..OFF_CREATOR + 32].copy_from_slice(&target);
    written[OFF_CASHBACK] = u8::from(cashback);
    written[OFF_CAN_EDIT] = 0;
    written[OFF_HOLDER] = u8::from(holder);
    let old_fee = read_u64(input.curve, OFF_FEE_BPS);
    let new_fee = fee.unwrap_or(old_fee);
    if fee.is_some() {
        written[OFF_FEE_BPS..OFF_FEE_BPS + 8].copy_from_slice(&new_fee.to_le_bytes());
    }
    let pool_updated = accounts.pool_nonempty && accounts.pool_owner_amm;
    Outcome::Ok {
        curve: written,
        event: event(
            input.timestamp,
            input.admin,
            input.mint,
            input.curve_key,
            old_creator,
            target,
            holder,
            cashback,
            old_fee,
            new_fee,
            sharing_reset,
            pool_updated,
        ),
        rent: due,
    }
}
