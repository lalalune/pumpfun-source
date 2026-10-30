//! Captured behavior of Pump `claim_cashback`: paying a user the SOL their
//! UserVolumeAccumulator (UVA) holds above its own rent-exempt minimum.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_claim_cashback_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.

/// Anchor `ConstraintMut`.
pub const CONSTRAINT_MUT: u32 = 2000;
/// Anchor `ConstraintSeeds`.
pub const CONSTRAINT_SEEDS: u32 = 2006;
/// Anchor `AccountDiscriminatorNotFound`.
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
/// Anchor `AccountDiscriminatorMismatch`.
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
/// Anchor `AccountDidNotDeserialize`.
pub const DID_NOT_DESERIALIZE: u32 = 3003;
/// Anchor `AccountOwnedByWrongProgram`.
pub const WRONG_OWNER: u32 = 3007;
/// Anchor `AccountNotInitialized`.
pub const NOT_INITIALIZED: u32 = 3012;
pub const OVERFLOW: u32 = 6024;

/// Default-rent cost of one byte: `Rent::minimum_balance(len) == (128 + len) * 6960`.
pub const LAMPORTS_PER_BYTE: u64 = 6_960;
/// Discriminator plus the serialized UVA fields; shorter data does not decode.
pub const UVA_DECODED_LEN: usize = 106;
pub const UVA_DISC: [u8; 8] = [86, 255, 112, 14, 102, 53, 154, 250];
const CLAIM_EVENT: [u8; 8] = [226, 214, 246, 33, 7, 242, 147, 229];

const OFF_NEEDS_CLAIM: usize = 40;
const OFF_HAS_TOTAL_CLAIMED: usize = 73;
const OFF_CASHBACK_EARNED: usize = 74;
const OFF_TOTAL_CASHBACK_CLAIMED: usize = 82;

pub struct Claim<'a> {
    pub user: [u8; 32],
    pub user_writable: bool,
    /// UVA lamports (0: the account does not exist).
    pub uva_lamports: u64,
    pub uva_owned_by_pump: bool,
    /// The UVA key is the `["user_volume_accumulator", user]` PDA.
    pub uva_is_user_pda: bool,
    pub uva_writable: bool,
    pub uva_data: &'a [u8],
}

#[derive(Debug, PartialEq, Eq)]
pub struct Claimed {
    /// Lamports moved from the UVA to the user (0: no transfer, no event).
    pub amount: u64,
    /// UVA bytes after the instruction.
    pub uva_data: Vec<u8>,
    pub event: Option<Vec<u8>>,
}

fn u64_at(data: &[u8], offset: usize) -> u64 {
    u64::from_le_bytes(data[offset..offset + 8].try_into().unwrap())
}

/// Anchor `Account<UserVolumeAccumulator>` loading.
fn load_uva(c: &Claim) -> Result<(), u32> {
    if c.uva_lamports == 0 {
        return Err(NOT_INITIALIZED);
    }
    if !c.uva_owned_by_pump {
        return Err(WRONG_OWNER);
    }
    if c.uva_data.len() < 8 {
        return Err(DISCRIMINATOR_NOT_FOUND);
    }
    if c.uva_data[..8] != UVA_DISC {
        return Err(DISCRIMINATOR_MISMATCH);
    }
    if c.uva_data.len() < UVA_DECODED_LEN || c.uva_data[OFF_NEEDS_CLAIM] > 1 || c.uva_data[OFF_HAS_TOTAL_CLAIMED] > 1 {
        return Err(DID_NOT_DESERIALIZE);
    }
    Ok(())
}

/// Order (each confirmed on the captured program): the UVA loads (missing,
/// owner, discriminator, decode) before any constraint; then `user` mut; then
/// UVA seeds before UVA mut. The stored `user` field is never compared with
/// the `user` account. The claim is the UVA's lamports above
/// `Rent::minimum_balance(uva data length)` (saturating; the full allocated
/// length counts, not just the decoded 106 bytes). `cashback_earned` does not
/// limit it. A zero claim returns before the overflow check and emits nothing.
pub fn claim(c: &Claim, timestamp: i64) -> Result<Claimed, u32> {
    load_uva(c)?;
    if !c.user_writable {
        return Err(CONSTRAINT_MUT);
    }
    if !c.uva_is_user_pda {
        return Err(CONSTRAINT_SEEDS);
    }
    if !c.uva_writable {
        return Err(CONSTRAINT_MUT);
    }
    let minimum = (128 + c.uva_data.len() as u64) * LAMPORTS_PER_BYTE;
    let amount = c.uva_lamports.saturating_sub(minimum);
    let mut data = c.uva_data.to_vec();
    if amount == 0 {
        return Ok(Claimed { amount, uva_data: data, event: None });
    }
    let total_claimed = u64_at(&data, OFF_TOTAL_CASHBACK_CLAIMED).checked_add(amount).ok_or(OVERFLOW)?;
    data[OFF_TOTAL_CASHBACK_CLAIMED..OFF_TOTAL_CASHBACK_CLAIMED + 8].copy_from_slice(&total_claimed.to_le_bytes());
    let mut event = Vec::with_capacity(72);
    event.extend_from_slice(&CLAIM_EVENT);
    event.extend_from_slice(&c.user);
    event.extend_from_slice(&amount.to_le_bytes());
    event.extend_from_slice(&timestamp.to_le_bytes());
    event.extend_from_slice(&total_claimed.to_le_bytes());
    event.extend_from_slice(&u64_at(&data, OFF_CASHBACK_EARNED).to_le_bytes());
    Ok(Claimed { amount, uva_data: data, event: Some(event) })
}
