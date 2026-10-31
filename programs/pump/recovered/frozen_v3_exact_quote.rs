//! Captured effect of a frozen token account on Pump's exact-quote buys
//! (`buy_exact_quote_in_v3` and the crossing `buy_v3`; both run their legs
//! through `v3_execute_buy`): which failures still win, and where SPL
//! Token's `AccountFrozen` takes over.
//!
//! A trade never reads the `state` byte itself, so the answer depends on
//! the order the handler runs its token transfers — the base leg, the
//! quote leg and the buyback leg — and on how far the unfrozen twin got.
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_frozen_v3_exact_quote_captured.py`, which reruns every
//! fixed and random case of `tests/test_v3_exact_quote_captured.py` with
//! one token account frozen. Not linked into the SBF crate. This is not a
//! byte-identity claim.
//!
//! Each leg's transfer helper returns before invoking the token program
//! when its amount is zero (`v2_transfer_curve_tokens`,
//! `v2_transfer_quote_tokens` and `collect_transfer_user_quote_tokens` in
//! `util/payments.rs`), so a leg runs exactly when its GROSS amount is
//! positive — not when the account it touches ends up moving on net:
//!
//! - the base leg's gross is the curve fill plus the post-complete fill
//!   (the `delivered` sum the handler checks the curve vault against),
//!   while the accounting model records only the curve fill as
//!   `base_moved`. A plain crossing with zero curve fill therefore still
//!   runs its base transfer; a Mayhem crossing admits no post-complete
//!   fill, its delivered sum is zero and the base leg truly never runs.
//! - the quote leg's gross is `pool_quote`, before the quote mint's
//!   transfer fee is withheld from what the curve receives.
//! - the buyback leg's gross is the total buyback before withholding. A
//!   buyback whose transfer fee withholds everything lands zero on the
//!   recipient, but the transfer still ran with the gross amount.
//!
//! Judging a leg by the net delta of the account it touches gets all
//! three wrong, which is why this model takes the execution record —
//! each leg's gross amount — instead of the accounting model's deltas.
//! Failing twins supply actual invoked-leg identities from their inner
//! instructions: zero-amount earlier legs may have been skipped. This is
//! conditional on the unfrozen captured twin, not an independent handler.
//! It is the companion of `frozen_v3_trade.rs`, which covers `buy_v3` /
//! `sell_v3` over the trade-accounting cases; the handlers share
//! `v3_execute_buy`, but that model's inputs are net deltas, and on the
//! exact-quote cases the deltas cannot say whether a leg ran.
//!
//! The native-SOL route has no quote or buyback token accounts; only the
//! base leg applies there.

/// SPL Token `AccountFrozen`.
pub const ACCOUNT_FROZEN: u32 = 17;
/// SPL Token `InsufficientFunds`, the one non-Pump error the twins produce.
pub const INSUFFICIENT_FUNDS: u32 = 1;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Account {
    /// Base leg: the user's base token account.
    UserBase,
    /// Base leg: the curve's base token account.
    CurveBase,
    /// Quote leg: the user's quote token account (the leg's source).
    UserQuote,
    /// Quote leg: the curve's quote token account (the leg's destination).
    CurveQuote,
    /// Buyback leg: the buyback recipient's quote token account
    /// (the leg's destination).
    Recipient,
}

impl Account {
    /// Transfer order of this account's leg: base, quote, buyback.
    fn leg(self) -> u32 {
        match self {
            Account::UserBase | Account::CurveBase => 1,
            Account::UserQuote | Account::CurveQuote => 2,
            Account::Recipient => 3,
        }
    }
}

/// How the same trade ends with no account frozen.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Unfrozen {
    Done,
    Code(u32),
}

/// The unfrozen twin's execution record: how much each leg was asked to
/// move, and how far the twin actually got.
#[derive(Clone, Copy, Debug)]
pub struct Execution {
    /// Gross base transfer: curve fill plus post-complete fill.
    pub base_gross: u64,
    /// Gross quote transfer (`pool_quote`, before the transfer fee).
    pub quote_gross: u64,
    /// Gross buyback transfer (before the transfer fee is withheld).
    pub buyback_gross: u64,
    /// Actual unfrozen token CPI legs: bit 0 base, bit 1 quote, bit 2 buyback.
    /// A skipped zero leg is absent; invocation count cannot identify it.
    pub invoked_legs: u8,
    /// Whether the quote legs run under Token-2022 (the base leg always
    /// runs under SPL Token).
    pub token_2022: bool,
}

impl Execution {
    /// Whether the leg's transfer is invoked at all: its helper returns
    /// early on a zero gross amount.
    fn runs(&self, leg: u32) -> bool {
        match leg {
            1 => self.base_gross > 0,
            2 => self.quote_gross > 0,
            _ => self.buyback_gross > 0,
        }
    }
}

/// How the trade ends with `account` frozen.
pub fn frozen(account: Account, unfrozen: Unfrozen, exec: Execution) -> Unfrozen {
    let leg = account.leg();
    match unfrozen {
        Unfrozen::Done => {
            // A frozen account fails its leg only if the leg's transfer
            // actually runs; a leg whose gross amount is zero is never
            // invoked, so the trade still succeeds (the Mayhem crossing's
            // base leg, an empty buyback share, the mayhem and whitelisted
            // routes' empty buyback leg).
            if exec.runs(leg) {
                Unfrozen::Code(ACCOUNT_FROZEN)
            } else {
                Unfrozen::Done
            }
        }
        Unfrozen::Code(code) if code == INSUFFICIENT_FUNDS => {
            // The twin died inside a token transfer, the last one it
            // started. An earlier leg's frozen account fails first; a later
            // leg is never reached.
            let bit = 1 << (leg - 1);
            if exec.invoked_legs & bit == 0 {
                return Unfrozen::Code(code);
            }
            let last_leg = 8 - exec.invoked_legs.leading_zeros();
            if leg < last_leg {
                return Unfrozen::Code(ACCOUNT_FROZEN);
            }
            if leg > last_leg {
                return Unfrozen::Code(code);
            }
            // The frozen account sits on the failing leg itself. SPL Token
            // checks the frozen state before the balance, so the frozen
            // error wins there. A Token-2022 quote leg checks the amount
            // before the destination's state, so its destination keeps the
            // twin's error while its source still turns frozen.
            if leg == 1 || !exec.token_2022 || account == Account::UserQuote {
                Unfrozen::Code(ACCOUNT_FROZEN)
            } else {
                Unfrozen::Code(code)
            }
        }
        Unfrozen::Code(code) => {
            // A Pump error wins unless a transfer already ran ahead of it.
            // In the checked inputs only the fee-accrual overflow (6024)
            // is raised after a transfer — the base leg, one invocation —
            // so exactly that leg turns frozen and the later legs keep the
            // error. Every other failing twin starts no transfer at all.
            if exec.invoked_legs & (1 << (leg - 1)) != 0 {
                Unfrozen::Code(ACCOUNT_FROZEN)
            } else {
                Unfrozen::Code(code)
            }
        }
    }
}
