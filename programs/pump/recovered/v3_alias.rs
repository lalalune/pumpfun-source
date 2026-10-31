//! Captured behavior of Pump `sell_v3`, `buy_v3` and `buy_exact_quote_in_v3`
//! when `Global.buyback_fee_recipient` names a key that is also another
//! account of the trade, or when the buyer passes the curve's token account.
//! Pricing is not modelled here: `baseline` is the settlement that
//! `v3_trade_accounting.rs` or `v3_exact_quote.rs` gives the same trade with
//! an ordinary recipient, and this file says what changes.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_v3_alias_captured.py`. Not linked into the SBF crate. This is
//! not a byte-identity claim.
//!
//! Observed rules:
//! - Pricing, the stored curve and the events do not change, and each key's
//!   balance is the sum of its slots. The buyer can be the recipient, and on
//!   a token curve the recipient's token account can be the curve's or the
//!   buyer's.
//! - The Pump program key is `ConstraintMut` (2000) on a SOL curve only, where
//!   the slot is the key itself; on a token curve the slot is the key's token
//!   account. Then come the entry guards 6005 and 6094, the buyer's quote
//!   account (6010), the all-zero recipient (6062) and the priced stops.
//! - The event authority cannot take SOL: a non-zero share fails with
//!   `UnbalancedInstruction`. On a token curve it is an ordinary owner.
//! - A buyer's base account that is the curve's own: a buy moves the reserves
//!   and charges the buyer, but no token leaves the account; a sell fails with
//!   SPL Token error 4. A buyer's quote account that is the curve's is 6010.

pub const CONSTRAINT_MUT: u32 = 2000;
pub const COMPLETE: u32 = 6005;
pub const CASHBACK: u32 = 6094;
pub const BUYBACK_RECIPIENT_UNSET: u32 = 6062;
pub const QUOTE_ACCOUNT: u32 = 6010;
pub const TOKEN_OWNER_MISMATCH: u32 = 4;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Role {
    Ordinary,
    User,
    Curve,
    EventAuthority,
    Program,
    Zero,
}

/// Quote amounts as the base models report them: signed, seen from each slot.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Settled {
    pub user_quote: i128,
    pub curve_quote: i128,
    pub recipient: i128,
    pub rent_top_up: i128,
    pub base_moved: i128,
}

pub struct Case {
    pub role: Role,
    pub native: bool,
    pub sell: bool,
    pub user_base_is_curves: bool,
    pub user_quote_is_curves: bool,
    pub baseline: Result<Settled, u32>,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    UnbalancedInstruction,
}

/// Signed balance changes. The transaction fee is not counted.
#[derive(Debug, Default, PartialEq, Eq)]
pub struct Moved {
    pub user_lamports: i128,
    pub curve_lamports: i128,
    pub recipient_lamports: i128,
    pub user_base: i128,
    pub curve_base: i128,
    pub user_quote: i128,
    pub curve_quote: i128,
    pub recipient_quote: i128,
}

pub fn trade(c: &Case) -> Result<Moved, Stop> {
    if c.role == Role::Program && c.native {
        return Err(Stop::Code(CONSTRAINT_MUT));
    }
    if let Err(code @ (COMPLETE | CASHBACK)) = c.baseline {
        return Err(Stop::Code(code));
    }
    if c.user_quote_is_curves {
        return Err(Stop::Code(QUOTE_ACCOUNT));
    }
    if c.role == Role::Zero {
        return Err(Stop::Code(BUYBACK_RECIPIENT_UNSET));
    }
    let s = c.baseline.map_err(Stop::Code)?;
    if c.user_base_is_curves && c.sell {
        return Err(Stop::Code(TOKEN_OWNER_MISMATCH));
    }
    if c.native && c.role == Role::EventAuthority && s.recipient != 0 {
        return Err(Stop::UnbalancedInstruction);
    }
    let mut m = Moved::default();
    let signed = if c.sell { -s.base_moved } else { s.base_moved };
    if !c.user_base_is_curves {
        m.user_base = signed;
        m.curve_base = -signed;
    }
    m.user_lamports = -s.rent_top_up;
    m.curve_lamports = s.rent_top_up;
    if c.native {
        m.user_lamports += s.user_quote;
        m.curve_lamports += s.curve_quote;
        m.recipient_lamports = s.recipient;
        match c.role {
            Role::User => m.user_lamports += s.recipient,
            Role::Curve => m.curve_lamports += s.recipient,
            _ => {}
        }
    } else {
        m.user_quote = s.user_quote;
        m.curve_quote = s.curve_quote;
        m.recipient_quote = s.recipient;
        match c.role {
            Role::User => m.user_quote += s.recipient,
            Role::Curve => m.curve_quote += s.recipient,
            _ => {}
        }
    }
    Ok(m)
}
