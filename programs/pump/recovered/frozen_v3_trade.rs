//! Captured effect of a frozen token account on Pump's v3 trades
//! (`buy_v3` / `sell_v3`): which failures still win, and where SPL Token's
//! `AccountFrozen` takes over.
//!
//! A trade never reads the `state` byte itself, so the answer depends on the
//! order the handler runs its token transfers — the base leg, the quote leg
//! and the buyback leg — and on how far the unfrozen twin got. Checked
//! against `evidence/original/pump/deployed.so` by
//! `tests/test_frozen_v3_trade_captured.py`, which reruns every fixed case
//! of `tests/test_v3_trade_accounting_captured.py` with one token account
//! frozen. Not linked into the SBF crate. This is not a byte-identity claim.
//!
//! The native-SOL route has no quote or buyback token accounts; only the
//! base leg applies there. `frozen_trade.rs` covers the legacy and v2
//! handlers; the two models share no answers, because the v3 handlers run
//! their legs in a different order around their own checks.

/// SPL Token `AccountFrozen`.
pub const ACCOUNT_FROZEN: u32 = 17;
/// SPL Token `InsufficientFunds`, the one non-Pump error the twins produce.
pub const INSUFFICIENT_FUNDS: u32 = 1;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Side {
    Buy,
    Sell,
}

/// One token account a v3 trade can touch. The legs run in the order base,
/// quote, buyback; an account also sits on one side of its leg.
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

/// Facts about the unfrozen twin run that the frozen answer depends on.
#[derive(Clone, Copy, Debug)]
pub struct Twin {
    /// Token-program invocations the twin started. A failing twin's last
    /// invocation is the transfer that failed; a Pump error raised after
    /// some transfers leaves that many invocations behind it.
    pub invokes: u32,
    /// On a `Done` twin, whether the quote leg moves any tokens.
    pub quote_moves: bool,
    /// On a `Done` twin, whether the buyback leg moves any tokens.
    pub buyback_moves: bool,
    /// Whether the quote legs run under Token-2022 (the base leg always
    /// runs under SPL Token).
    pub token_2022: bool,
}

/// How the trade ends with `account` frozen.
pub fn frozen(side: Side, account: Account, unfrozen: Unfrozen, twin: Twin) -> Unfrozen {
    let leg = account.leg();
    match unfrozen {
        Unfrozen::Done => {
            // A frozen account fails its leg only if the leg actually moves
            // tokens through it; an empty leg is never transferred, so the
            // trade still succeeds (a zero quote leg, a zero buyback share,
            // the mayhem and whitelisted routes' empty buyback leg).
            let moves = match leg {
                1 => true,
                2 => twin.quote_moves,
                _ => twin.buyback_moves,
            };
            if moves {
                Unfrozen::Code(ACCOUNT_FROZEN)
            } else {
                Unfrozen::Done
            }
        }
        Unfrozen::Code(code) if code == INSUFFICIENT_FUNDS && side == Side::Buy => {
            // The twin died inside a token transfer, the last one it
            // started. An earlier leg's frozen account fails first; a later
            // leg is never reached.
            if leg < twin.invokes {
                return Unfrozen::Code(ACCOUNT_FROZEN);
            }
            if leg > twin.invokes {
                return Unfrozen::Code(code);
            }
            // The frozen account sits on the failing leg itself. SPL Token
            // checks the frozen state before the balance, so the frozen
            // error wins there. A Token-2022 quote leg checks the amount
            // before the destination's state, so its destination keeps the
            // twin's error while its source still turns frozen.
            if leg == 1 || !twin.token_2022 || account == Account::UserQuote {
                Unfrozen::Code(ACCOUNT_FROZEN)
            } else {
                Unfrozen::Code(code)
            }
        }
        Unfrozen::Code(code) => {
            // A Pump error wins unless a transfer already ran ahead of it.
            // In the checked inputs only the fee-accrual overflow (6024) on
            // token-quote routes is raised after transfers — the base and
            // quote legs, two invocations — so exactly those two legs turn
            // frozen and the buyback leg keeps the error. Every other
            // failing twin starts no transfer at all.
            if twin.invokes > 0 && leg <= twin.invokes {
                Unfrozen::Code(ACCOUNT_FROZEN)
            } else {
                Unfrozen::Code(code)
            }
        }
    }
}
