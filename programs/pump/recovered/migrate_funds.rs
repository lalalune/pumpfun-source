//! Captured funding rules of Pump `migrate`, which `migrate.rs` lists as
//! unconfirmed: curve accounts shorter or longer than 166 bytes, the rent
//! top-up, a curve holding less than it owes, a `pool_migration_fee` too small
//! to pay for the pool's token accounts, and a non-zero base balance.
//!
//! Account checks, the completion gate, the quote amount and the boost gate stay
//! in `migrate.rs`; this file only puts the money steps between them.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_migrate_funds_captured.py`, with pump_amm replaced by the no-op
//! program of `tests/test_migrate_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): the outcome of a non-zero
//! base balance with a real pump_amm. The no-op takes nothing, so such a run
//! stops at the close; only the amount it sends is confirmed. Pre-existing pool
//! token accounts and a user too poor for the top-up are outside too, and so
//! are the exact length at which the fee buckets start to be read here (the 141
//! comes from `multi_hop_accounts.rs`) and the rent limit of a curve longer than
//! 166 bytes that ends below it.

use crate::migrate::{self, Fault, Migrate, Outcome, Stop, OVERFLOW};

/// System `InsufficientFunds`: the fee cannot pay for the token accounts.
pub const SYSTEM_INSUFFICIENT_FUNDS: u32 = 1;
/// SPL Token `NonNativeHasBalance`, closing the pool authority's base account.
pub const NON_NATIVE_HAS_BALANCE: u32 = 11;
/// Rent of the four token accounts the fee pays for.
pub const TOKEN_ACCOUNTS_COST: u64 = 4 * 2_039_280;
/// `Rent::minimum_balance(165)`, sent to the pool authority for `init_boost`.
pub const BOOST_FUNDING: u64 = 2_039_280;
pub const CURVE_LEN: usize = 166;
pub const CURVE_MIN_LEN: usize = 49;

/// `Rent::minimum_balance(len)`.
pub fn rent(len: usize) -> u64 {
    (128 + len as u64) * 6_960
}

pub struct Funds {
    pub curve_len: usize,
    pub curve_lamports: u64,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    /// Balance of the curve's base token account.
    pub base_balance: u64,
    pub has_creator: bool,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Failure {
    Stop(Stop),
    /// The curve's data does not deserialize.
    InvalidData,
    /// A lamport subtraction on the curve underflows.
    Lamports,
    /// The quote leaves the curve below its rent: the runtime refuses the
    /// transaction before any later error of the program can show.
    BelowRent,
    /// `create_pool`, and `init_boost` if the flag says so, were sent with this
    /// base amount before the error.
    AfterPool(u32, u64, bool),
}

#[derive(Debug, PartialEq, Eq)]
pub struct Moved {
    pub outcome: Outcome,
    pub base_amount_in: u64,
    /// Lamports the user paid: the top-up and the boost funding.
    pub user_paid: u64,
    pub creator: bool,
}

/// A field past the end of the curve reads as zero.
fn read(m: &mut Migrate, f: &mut Funds) {
    let len = f.curve_len;
    if len < 81 {
        f.has_creator = false;
    }
    if len < 82 {
        m.is_mayhem_mode = false;
    }
    if len < 83 {
        m.is_cashback_coin = false;
    }
    // A quote mint past the end reads as native.
    if len < 115 {
        m.faults.retain(|&x| x != Fault::CurveQuoteMint);
    }
    // Read together, so 123 bytes do not give the fee.
    if len < 124 {
        m.creator_fee_bps = 0;
        m.can_edit_creator_fee = false;
    }
    if len < 125 {
        m.is_holder_reward = false;
    }
    if len < 141 {
        f.creator_fee = 0;
        f.protocol_fees = 0;
    }
    if len < 166 {
        m.post_complete_quote_in = 0;
    }
}

fn stop(s: Stop) -> Failure {
    Failure::Stop(s)
}

pub fn run(mut m: Migrate, mut f: Funds) -> Result<Moved, Failure> {
    if f.curve_len < CURVE_MIN_LEN {
        return Err(Failure::InvalidData);
    }
    read(&mut m, &mut f);
    if m.complete > 1 || !m.faults.is_empty() {
        return migrate::migrate(&m).map(|_| unreachable!()).map_err(stop);
    }
    let owed = m
        .real_quote_reserves
        .checked_add(f.creator_fee)
        .and_then(|v| v.checked_add(f.protocol_fees))
        .ok_or(stop(Stop::Code(OVERFLOW)))?;
    let len = f.curve_len.max(CURVE_LEN);
    let need = rent(len).saturating_sub(f.curve_lamports.saturating_sub(owed));
    let lamports = f.curve_lamports + need;
    let creator = f.has_creator;
    let done = |outcome, base_amount_in, boost: bool| {
        let user_paid = need + if boost { BOOST_FUNDING } else { 0 };
        Ok(Moved { outcome, base_amount_in, user_paid, creator })
    };
    if m.complete == 0 {
        return Err(stop(Stop::Code(migrate::BONDING_CURVE_NOT_COMPLETE)));
    }
    if m.virtual_token_reserves == 0 && m.virtual_quote_reserves == 0 && m.real_token_reserves == 0 && m.real_quote_reserves == 0 {
        return done(Outcome::AlreadyMigrated, 0, false);
    }
    let left = lamports.checked_sub(m.pool_migration_fee).ok_or(Failure::Lamports)?;
    if m.pool_migration_fee < TOKEN_ACCOUNTS_COST {
        return Err(stop(Stop::Code(SYSTEM_INSUFFICIENT_FUNDS)));
    }
    // Added before the fee is taken back, as `migrate.rs` says.
    let total = m.real_quote_reserves.checked_add(m.post_complete_quote_in).ok_or(stop(Stop::Code(OVERFLOW)))?;
    let quote = total.checked_sub(m.pool_migration_fee).ok_or(stop(Stop::Code(OVERFLOW)))?;
    let left = left.checked_sub(quote).ok_or(Failure::Lamports)?;
    // A curve left with nothing is rent-free; the account goes away.
    if left != 0 && left < rent(len) {
        return Err(Failure::BelowRent);
    }
    let mut outcome = migrate::migrate(&m).map_err(|e| match e {
        Stop::Code(code) if code == migrate::NOT_ENOUGH_REMAINING_ACCOUNTS => Failure::AfterPool(code, f.base_balance, false),
        other => stop(other),
    })?;
    let boost = matches!(outcome, Outcome::Migrated { init_boost: true, .. });
    if f.base_balance != 0 {
        return Err(Failure::AfterPool(NON_NATIVE_HAS_BALANCE, f.base_balance, boost));
    }
    if let Outcome::Migrated { curve_lamports, .. } = &mut outcome {
        *curve_lamports = left;
    }
    done(outcome, f.base_balance, boost)
}
