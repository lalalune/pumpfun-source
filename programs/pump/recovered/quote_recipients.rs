//! Recipient admission of `sell_v2`, `buy_v2` and `buy_exact_quote_in_v2` on
//! token quotes, for ordinary and whitelisted users, over any `Global` key
//! lists: which keys pass, how that ranks against the recipients' quote token
//! accounts, and who is paid.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_quote_recipients_captured.py`, on wSOL, USDC, SPL
//! and Token-2022 quotes. Not linked into the SBF crate. This is not a
//! byte-identity claim.
//!
//! `Global.fee_recipients` is searched with the left/right form of slice binary
//! search, which stops at the first equal probe, so on an unsorted list a
//! member can be refused. Keys compare as big-endian byte strings. The reserved
//! and buyback lists are scanned linearly, so their order does not matter.
//!
//! Unconfirmed (미확인, outside the checked inputs): the native routes, the v3
//! handlers, `multi_hop_curve_swap`, and a recipient account that exists with
//! the wrong mint or owner.

pub const NOT_AUTHORIZED: u32 = 6000;
/// Anchor `ConstraintSeeds`.
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED: u32 = 6057;
pub const BUYBACK_FEE_RECIPIENT_MISSING: u32 = 6062;

pub type Key = [u8; 32];
pub const ZERO: Key = [0; 32];

/// The `Global` fields the checks read.
pub struct Recipients {
    pub fee_recipient: Key,
    pub fee_recipients: [Key; 7],
    pub reserved_fee_recipient: Key,
    pub reserved_fee_recipients: [Key; 7],
    pub buyback_fee_recipients: [Key; 8],
}

/// The quote token account passed for a recipient.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum QuoteAccount {
    /// The recipient's associated token account, already there.
    Present,
    /// The right address, with nothing there yet.
    Absent,
    /// Another address.
    WrongAddress,
}

pub struct Trade {
    pub whitelisted: bool,
    pub mayhem: bool,
    pub buyback_bps: u64,
    pub fee_key: Key,
    pub buyback_key: Key,
    pub fee_account: QuoteAccount,
    pub buyback_account: QuoteAccount,
}

/// Who is paid and which quote accounts the trade creates.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Settled {
    pub fee_paid: bool,
    pub buyback_paid: bool,
    pub fee_account_created: bool,
    pub buyback_account_created: bool,
}

/// The original search: the probe at `left + size / 2` ends the loop on equal.
fn searched(list: &[Key; 7], key: &Key) -> bool {
    let mut size = list.len();
    let mut left = 0;
    let mut right = size;
    while left < right {
        let mid = left + size / 2;
        if list[mid] < *key {
            left = mid + 1;
        } else if list[mid] > *key {
            right = mid;
        } else {
            return true;
        }
        size = right - left;
    }
    false
}

/// A Mayhem curve takes only the reserved keys, any other curve only
/// `fee_recipient` and `fee_recipients`.
pub fn fee_recipient_ok(r: &Recipients, mayhem: bool, key: &Key) -> bool {
    if mayhem {
        *key == r.reserved_fee_recipient || r.reserved_fee_recipients.contains(key)
    } else {
        *key == r.fee_recipient || searched(&r.fee_recipients, key)
    }
}

/// The zero key is refused before the list is read, even when the list holds
/// zero keys.
pub fn check_buyback(r: &Recipients, key: &Key) -> Result<(), u32> {
    if *key == ZERO {
        return Err(BUYBACK_FEE_RECIPIENT_MISSING);
    }
    if !r.buyback_fee_recipients.contains(key) {
        return Err(BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED);
    }
    Ok(())
}

/// The checks in program order. The token account addresses are account
/// constraints, so they rank ahead of both keys, and the whitelisted user goes
/// through the same checks although it pays neither recipient.
pub fn admit(r: &Recipients, t: &Trade) -> Result<Settled, u32> {
    if t.fee_account == QuoteAccount::WrongAddress || t.buyback_account == QuoteAccount::WrongAddress {
        return Err(CONSTRAINT_SEEDS);
    }
    if !fee_recipient_ok(r, t.mayhem, &t.fee_key) {
        return Err(NOT_AUTHORIZED);
    }
    check_buyback(r, &t.buyback_key)?;
    Ok(Settled {
        fee_paid: !t.whitelisted,
        buyback_paid: !t.whitelisted && !t.mayhem && t.buyback_bps > 0,
        fee_account_created: t.fee_account == QuoteAccount::Absent,
        buyback_account_created: t.buyback_account == QuoteAccount::Absent,
    })
}
