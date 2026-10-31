//! Captured effect of a frozen token account on Pump's native trades: which
//! failures still win, and where SPL Token's `AccountFrozen` takes over.
//!
//! A trade never reads the `state` byte itself, so the answer depends only on
//! whether the token transfer runs. Checked against
//! `evidence/original/pump/deployed.so` by `tests/test_frozen_trade_captured.py`,
//! which reruns the fixed cases of the legacy and v2 trade tests with one token
//! account frozen. Not linked into the SBF crate. This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): v3 handlers, token quotes,
//! Token-2022 accounts, and whitelisted or Mayhem routes.

/// SPL Token `AccountFrozen`.
pub const ACCOUNT_FROZEN: u32 = 17;
/// `sell` checks that run after the tokens have moved.
pub const SELL_AFTER_TRANSFER: [u32; 3] = [6057, 6062, 6074];
/// The same for `sell_v2`, whose buyback recipient check (6057) comes first.
pub const SELL_V2_AFTER_TRANSFER: [u32; 2] = [6062, 6074];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Side {
    Buy,
    Sell,
    SellV2,
}

/// How the same trade ends with no account frozen.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Unfrozen {
    Done,
    Code(u32),
    /// A panic; `transfer_ran` says whether the token transfer came first.
    Panic { transfer_ran: bool },
}

/// How the trade ends with the curve's or the user's token account frozen.
/// Either account gives the same answer.
pub fn frozen(side: Side, unfrozen: Unfrozen) -> Unfrozen {
    let reached = match unfrozen {
        Unfrozen::Done => true,
        Unfrozen::Code(code) => match side {
            Side::Buy => false,
            Side::Sell => SELL_AFTER_TRANSFER.contains(&code),
            Side::SellV2 => SELL_V2_AFTER_TRANSFER.contains(&code),
        },
        Unfrozen::Panic { transfer_ran } => transfer_ran,
    };
    if reached {
        Unfrozen::Code(ACCOUNT_FROZEN)
    } else {
        unfrozen
    }
}
