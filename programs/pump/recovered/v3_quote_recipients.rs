//! Buyback recipient determination of `sell_v3`, `buy_v3` and
//! `buy_exact_quote_in_v3` on token quotes: which key the handler reads from
//! the recipient token account, how that key is judged against
//! `Global.buyback_fee_recipients`, and which account is then paid.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_v3_quote_recipients_captured.py`. Not linked into
//! the SBF crate. This is not a byte-identity claim.
//!
//! The neighbouring packets fix the rest of the picture, and this one does
//! not repeat them: `trade_recipients.rs` covers the native routes, where the
//! account key itself is judged; `v3_account_admission.rs` covers the v3
//! account slots — the recipient slot's address, program, mint and faults,
//! and the owner judgment for an owner entered at the last list slot.
//! `v3_trade_accounting.rs` prices the trades and pays the one fixture
//! recipient. What none of them varies is the list itself and the payment
//! together: the owner entered at each of the eight slots, entered twice, a
//! different listed owner than the fixture's, a whitelisted user, a mayhem
//! curve, and a trade whose buyback split is zero. The amounts are the
//! accounting fixture's fixed ones throughout; only the recipient moves.
//!
//! The v3 handlers take no fee-recipient account: the protocol fee accrues
//! on the curve (the accounting packet's picture), so the buyback recipient
//! is the only recipient a token-quote v3 trade pays.
//!
//! Unconfirmed (미확인, outside the checked inputs): recipient accounts of
//! any shape other than the owner's associated token account (the admission
//! packet's territory), and the native routes (the trade recipients packet's).

pub const BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED: u32 = 6057;
pub const BUYBACK_FEE_RECIPIENT_MISSING: u32 = 6062;

/// The recipient token account's owner, as judged. Where in the list a
/// listed owner sits, and whether it sits there twice, are fixture shapes
/// the test varies; the judgment has no input for them.
#[derive(Clone, Copy, Debug)]
pub struct Recipient {
    /// The owner is the zero key.
    pub zero: bool,
    /// The owner is one of the eight `buyback_fee_recipients` entries.
    pub listed: bool,
    /// A whitelisted user: admitted the same, paid nothing.
    pub whitelisted: bool,
}

/// Who is paid: the passed account, when the judgment passes and the trade
/// pays a buyback at all.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Settled {
    pub paid: bool,
}

/// The judgment in program order: the zero owner is refused before the list
/// is read, and the list check runs whether or not the trade would pay —
/// a whitelisted user, and a trade with a zero buyback split, are judged
/// exactly like any other.
pub fn judge(r: &Recipient) -> Result<Settled, u32> {
    if r.zero {
        return Err(BUYBACK_FEE_RECIPIENT_MISSING);
    }
    if !r.listed {
        return Err(BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED);
    }
    Ok(Settled { paid: !r.whitelisted })
}
