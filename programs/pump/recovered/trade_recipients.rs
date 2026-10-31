//! Recipient admission of the Pump trades and of `sweep_protocol_fee`, over any
//! `Global` key lists: which keys pass `validate_fee_recipient` and
//! `validate_buyback_fee_recipient`, and which of the two accounts is paid.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_trade_recipients_captured.py`, on the native quote
//! route of `buy`, `buy_exact_sol_in`, `sell`, `buy_v2`,
//! `buy_exact_quote_in_v2`, `sell_v2`, `buy_v3`, `buy_exact_quote_in_v3`,
//! `sell_v3`, and on `sweep_protocol_fee`.
//!
//! `Global.fee_recipients` is searched with the left/right form of slice binary
//! search, which stops at the first equal probe. `set_params` stores the list
//! sorted (6029), but the search does not depend on that: on an unsorted list a
//! member can be refused. Keys compare as big-endian byte strings. The reserved
//! and buyback lists are scanned linearly, so their order does not matter.
//! A trade admits the zero key like any other list member; only the payment
//! into the system program then fails, with no Pump error code.
//!
//! Unconfirmed (미확인, outside the checked inputs): token quotes (the v3
//! handlers then read the token account's owner), `multi_hop_curve_swap`, and
//! whitelisted users.

pub const NOT_AUTHORIZED: u32 = 6000;
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

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Route {
    /// `fee_recipient` first, then the buyback recipient.
    Trade,
    /// The v3 handlers name no fee recipient; the protocol fee stays on the curve.
    TradeV3,
    /// `sweep_protocol_fee`: `recipient` only.
    Sweep,
}

/// Which recipient receives quote once the checks pass.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Paid {
    pub fee_recipient: bool,
    pub buyback: bool,
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

/// `validate_fee_recipient`: a Mayhem curve takes only the reserved keys, any
/// other curve only `fee_recipient` and `fee_recipients`.
pub fn fee_recipient_ok(r: &Recipients, mayhem: bool, key: &Key) -> bool {
    if mayhem {
        *key == r.reserved_fee_recipient || r.reserved_fee_recipients.contains(key)
    } else {
        *key == r.fee_recipient || searched(&r.fee_recipients, key)
    }
}

/// `validate_buyback_fee_recipient`: the zero key is refused before the list is
/// read, even when the list holds zero keys. Mayhem curves run it too.
pub fn check_buyback(r: &Recipients, key: &Key) -> Result<(), u32> {
    if *key == ZERO {
        return Err(BUYBACK_FEE_RECIPIENT_MISSING);
    }
    if !r.buyback_fee_recipients.contains(key) {
        return Err(BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED);
    }
    Ok(())
}

/// The checks of one route, in program order. `Paid.buyback` is false on Mayhem
/// curves, which carry no buyback share.
pub fn admit(r: &Recipients, route: Route, mayhem: bool, fee_key: &Key, buyback_key: &Key) -> Result<Paid, u32> {
    match route {
        Route::Trade => {
            if !fee_recipient_ok(r, mayhem, fee_key) {
                return Err(NOT_AUTHORIZED);
            }
            check_buyback(r, buyback_key)?;
            Ok(Paid { fee_recipient: true, buyback: !mayhem })
        }
        Route::TradeV3 => {
            check_buyback(r, buyback_key)?;
            Ok(Paid { fee_recipient: false, buyback: !mayhem })
        }
        Route::Sweep => {
            // Unlike the trades, the sweep refuses the zero key before the lists.
            if *fee_key == ZERO || !fee_recipient_ok(r, mayhem, fee_key) {
                return Err(NOT_AUTHORIZED);
            }
            Ok(Paid { fee_recipient: true, buyback: false })
        }
    }
}
