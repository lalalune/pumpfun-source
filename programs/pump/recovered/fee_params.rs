//! Captured behavior of Pump `set_params` and `set_reserved_fee_recipients`:
//! the two Global setters that take their fee recipients from the first eight
//! remaining accounts.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_fee_params_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.

pub const IX_DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_RENT_EXEMPT: u32 = 2005;
pub const CONSTRAINT_EXECUTABLE: u32 = 2007;
pub const NOT_SIGNER: u32 = 3010;
pub const NOT_AUTHORIZED: u32 = 6000;
pub const REAL_TOKEN_NOT_BELOW_SUPPLY: u32 = 6011;
pub const VIRTUAL_TOKEN_NOT_ABOVE_REAL: u32 = 6012;
pub const FEE_BPS_ABOVE_MAXIMUM: u32 = 6013;
pub const ZERO_WITHDRAW_AUTHORITY: u32 = 6014;
pub const MIGRATION_FEE_NOT_BELOW_FINAL_SOL: u32 = 6015;
pub const TRUNCATION: u32 = 6025;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: u32 = 6027;
pub const ZERO_FEE_RECIPIENT: u32 = 6028;
pub const UNSORTED_FEE_RECIPIENTS: u32 = 6029;

/// Both basis-point arguments are capped at 1000 (inclusive).
pub const MAX_FEE_BPS: u64 = 1_000;
/// Default-rent cost of one byte: `Rent::minimum_balance(len) == (128 + len) * 6960`.
pub const LAMPORTS_PER_BYTE: u64 = 6_960;

const SET_PARAMS_EVENT: [u8; 8] = [223, 195, 159, 246, 62, 48, 143, 131];
const RESERVED_EVENT: [u8; 8] = [43, 188, 250, 18, 221, 75, 187, 95];

const OFF_FEE_RECIPIENT: usize = 41;
const OFF_INITIAL_RESERVES: usize = 73;
const OFF_WITHDRAW_AUTHORITY: usize = 113;
const OFF_ENABLE_MIGRATE: usize = 145;
const OFF_POOL_MIGRATION_FEE: usize = 146;
const OFF_CREATOR_FEE_BPS: usize = 154;
const OFF_FEE_RECIPIENTS: usize = 162;
const OFF_SET_CREATOR_AUTHORITY: usize = 386;
const OFF_ADMIN_SET_CREATOR_AUTHORITY: usize = 418;
const OFF_WHITELIST_PDA: usize = 451;
const OFF_RESERVED_FEE_RECIPIENT: usize = 483;
const OFF_RESERVED_FEE_RECIPIENTS: usize = 516;

pub type Key = [u8; 32];

/// One remaining account as the handler sees it.
#[derive(Clone, Copy)]
pub struct Recipient {
    pub key: Key,
    pub lamports: u64,
    pub data_len: u64,
    pub executable: bool,
}

impl Recipient {
    fn rent_exempt(&self) -> bool {
        self.lamports >= (128 + self.data_len) * LAMPORTS_PER_BYTE
    }
}

/// The admin accounts as the Anchor checks see them.
#[derive(Clone, Copy)]
pub struct Admin {
    pub authority_signs: bool,
    /// `global.authority == authority` (`has_one`).
    pub authority_matches: bool,
}

pub struct Params {
    pub initial_virtual_token_reserves: u64,
    pub initial_virtual_sol_reserves: u64,
    pub initial_real_token_reserves: u64,
    pub token_total_supply: u64,
    pub fee_basis_points: u64,
    pub withdraw_authority: Key,
    pub enable_migrate: bool,
    pub pool_migration_fee: u64,
    pub creator_fee_basis_points: u64,
    pub set_creator_authority: Key,
    pub admin_set_creator_authority: Key,
}

struct Reader<'a>(&'a [u8]);

impl Reader<'_> {
    fn take(&mut self, n: usize) -> Option<&[u8]> {
        if self.0.len() < n {
            return None;
        }
        let (head, rest) = self.0.split_at(n);
        self.0 = rest;
        Some(head)
    }
    fn u64(&mut self) -> Option<u64> {
        Some(u64::from_le_bytes(self.take(8)?.try_into().ok()?))
    }
    fn key(&mut self) -> Option<Key> {
        self.take(32)?.try_into().ok()
    }
    /// Borsh bool: only 0 and 1 decode.
    fn bool(&mut self) -> Option<bool> {
        match self.take(1)?[0] {
            0 => Some(false),
            1 => Some(true),
            _ => None,
        }
    }
}

/// Borsh decode of the `set_params` arguments (after the discriminator).
/// Bytes past the last argument are ignored.
pub fn decode_params(args: &[u8]) -> Result<Params, u32> {
    let mut r = Reader(args);
    let mut read = || -> Option<Params> {
        Some(Params {
            initial_virtual_token_reserves: r.u64()?,
            initial_virtual_sol_reserves: r.u64()?,
            initial_real_token_reserves: r.u64()?,
            token_total_supply: r.u64()?,
            fee_basis_points: r.u64()?,
            withdraw_authority: r.key()?,
            enable_migrate: r.bool()?,
            pool_migration_fee: r.u64()?,
            creator_fee_basis_points: r.u64()?,
            set_creator_authority: r.key()?,
            admin_set_creator_authority: r.key()?,
        })
    };
    read().ok_or(IX_DID_NOT_DESERIALIZE)
}

/// Borsh decode of the `set_reserved_fee_recipients` argument.
pub fn decode_whitelist(args: &[u8]) -> Result<Key, u32> {
    Reader(args).key().ok_or(IX_DID_NOT_DESERIALIZE)
}

/// Signer, then `has_one = authority`. The arguments decode before either.
fn check_admin(admin: Admin) -> Result<(), u32> {
    if !admin.authority_signs {
        return Err(NOT_SIGNER);
    }
    if !admin.authority_matches {
        return Err(NOT_AUTHORIZED);
    }
    Ok(())
}

/// The first eight remaining accounts; any further ones are ignored.
fn first_eight(remaining: &[Recipient]) -> Result<&[Recipient], u32> {
    remaining.get(..8).ok_or(NOT_ENOUGH_REMAINING_ACCOUNTS)
}

fn put(global: &mut [u8], offset: usize, bytes: &[u8]) {
    global[offset..offset + bytes.len()].copy_from_slice(bytes);
}

/// `set_params`: checks, then the Global writes and the SetParamsEvent bytes.
///
/// Order (each confirmed on the captured program): decode; signer; authority;
/// fewer than eight remaining accounts; any zero key among the eight (all
/// eight are checked before any rent check); each recipient rent-exempt in
/// index order (executable accounts are accepted); strictly ascending keys
/// (duplicates fail here too); `token_total_supply > initial_real_token_reserves`;
/// `initial_virtual_token_reserves > initial_real_token_reserves`;
/// `fee_basis_points <= 1000`; non-zero withdraw authority; the final real
/// SOL reserves fit in u64; `pool_migration_fee < final_real_sol_reserves`;
/// `creator_fee_basis_points <= 1000`.
pub fn set_params(
    admin: Admin,
    args: &[u8],
    remaining: &[Recipient],
    timestamp: i64,
    global: &mut [u8],
) -> Result<Vec<u8>, u32> {
    let p = decode_params(args)?;
    check_admin(admin)?;
    let recipients = first_eight(remaining)?;
    if recipients.iter().any(|r| r.key == [0; 32]) {
        return Err(ZERO_FEE_RECIPIENT);
    }
    if recipients.iter().any(|r| !r.rent_exempt()) {
        return Err(CONSTRAINT_RENT_EXEMPT);
    }
    if recipients.windows(2).any(|pair| pair[0].key >= pair[1].key) {
        return Err(UNSORTED_FEE_RECIPIENTS);
    }
    let (virtual_token, virtual_sol, real_token) =
        (p.initial_virtual_token_reserves, p.initial_virtual_sol_reserves, p.initial_real_token_reserves);
    if p.token_total_supply <= real_token {
        return Err(REAL_TOKEN_NOT_BELOW_SUPPLY);
    }
    if virtual_token <= real_token {
        return Err(VIRTUAL_TOKEN_NOT_ABOVE_REAL);
    }
    if p.fee_basis_points > MAX_FEE_BPS {
        return Err(FEE_BPS_ABOVE_MAXIMUM);
    }
    if p.withdraw_authority == [0; 32] {
        return Err(ZERO_WITHDRAW_AUTHORITY);
    }
    // u64 * u64 cannot overflow u128 and the divisor is non-zero after the
    // check above, so error6024 (Overflow) is unreachable here; only the
    // narrowing back to u64 can fail. The quotient rounds down.
    let quotient = real_token as u128 * virtual_sol as u128 / (virtual_token - real_token) as u128;
    let final_real_sol_reserves = u64::try_from(quotient).map_err(|_| TRUNCATION)?;
    if p.pool_migration_fee >= final_real_sol_reserves {
        return Err(MIGRATION_FEE_NOT_BELOW_FINAL_SOL);
    }
    if p.creator_fee_basis_points > MAX_FEE_BPS {
        return Err(FEE_BPS_ABOVE_MAXIMUM);
    }

    put(global, OFF_FEE_RECIPIENT, &recipients[0].key);
    for (i, r) in recipients[1..].iter().enumerate() {
        put(global, OFF_FEE_RECIPIENTS + 32 * i, &r.key);
    }
    for (i, value) in [virtual_token, virtual_sol, real_token, p.token_total_supply, p.fee_basis_points]
        .iter()
        .enumerate()
    {
        put(global, OFF_INITIAL_RESERVES + 8 * i, &value.to_le_bytes());
    }
    put(global, OFF_WITHDRAW_AUTHORITY, &p.withdraw_authority);
    global[OFF_ENABLE_MIGRATE] = p.enable_migrate as u8;
    put(global, OFF_POOL_MIGRATION_FEE, &p.pool_migration_fee.to_le_bytes());
    put(global, OFF_CREATOR_FEE_BPS, &p.creator_fee_basis_points.to_le_bytes());
    put(global, OFF_SET_CREATOR_AUTHORITY, &p.set_creator_authority);
    put(global, OFF_ADMIN_SET_CREATOR_AUTHORITY, &p.admin_set_creator_authority);

    let mut event = Vec::with_capacity(433);
    event.extend_from_slice(&SET_PARAMS_EVENT);
    for value in [virtual_token, virtual_sol, real_token, final_real_sol_reserves, p.token_total_supply, p.fee_basis_points] {
        event.extend_from_slice(&value.to_le_bytes());
    }
    event.extend_from_slice(&p.withdraw_authority);
    event.push(p.enable_migrate as u8);
    event.extend_from_slice(&p.pool_migration_fee.to_le_bytes());
    event.extend_from_slice(&p.creator_fee_basis_points.to_le_bytes());
    // All eight recipients, fee_recipient first.
    for r in recipients {
        event.extend_from_slice(&r.key);
    }
    event.extend_from_slice(&timestamp.to_le_bytes());
    event.extend_from_slice(&p.set_creator_authority);
    event.extend_from_slice(&p.admin_set_creator_authority);
    Ok(event)
}

/// `set_reserved_fee_recipients`: checks, then the Global writes and the
/// ReservedFeeRecipientsEvent bytes.
///
/// Order (each confirmed on the captured program): decode; signer; authority;
/// fewer than eight remaining accounts; then per recipient in index order:
/// zero key, executable, rent-exempt. Unlike `set_params`, keys need not be
/// sorted or unique.
pub fn set_reserved_fee_recipients(
    admin: Admin,
    args: &[u8],
    remaining: &[Recipient],
    timestamp: i64,
    global: &mut [u8],
) -> Result<Vec<u8>, u32> {
    let whitelist_pda = decode_whitelist(args)?;
    check_admin(admin)?;
    let recipients = first_eight(remaining)?;
    for r in recipients {
        if r.key == [0; 32] {
            return Err(ZERO_FEE_RECIPIENT);
        }
        if r.executable {
            return Err(CONSTRAINT_EXECUTABLE);
        }
        if !r.rent_exempt() {
            return Err(CONSTRAINT_RENT_EXEMPT);
        }
    }
    put(global, OFF_WHITELIST_PDA, &whitelist_pda);
    put(global, OFF_RESERVED_FEE_RECIPIENT, &recipients[0].key);
    for (i, r) in recipients[1..].iter().enumerate() {
        put(global, OFF_RESERVED_FEE_RECIPIENTS + 32 * i, &r.key);
    }
    let mut event = Vec::with_capacity(272);
    event.extend_from_slice(&RESERVED_EVENT);
    event.extend_from_slice(&timestamp.to_le_bytes());
    for r in recipients {
        event.extend_from_slice(&r.key);
    }
    Ok(event)
}
