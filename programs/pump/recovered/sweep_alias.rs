//! Captured behavior of Pump `sweep_protocol_fee` when `Global.fee_recipient`
//! (or, on a Mayhem curve, `Global.reserved_fee_recipient`) names a key that
//! is also another account of the call. Pricing and the ordinary stops come
//! from `sweep_fees.rs`.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_sweep_alias_captured.py`. Not linked into the SBF crate. This
//! is not a byte-identity claim.
//!
//! Observed rules:
//! - Lamports are additive per key. The payer may be the recipient, and a
//!   curve that receives its own fee keeps the lamports, but the bucket is
//!   still cleared, the event still fires and the curve's rent top-up is
//!   still paid. A curve short of the amount still fails the direct debit.
//! - On a token curve the recipient may be the curve: its token account is
//!   both ends, no token moves and no account is created.
//! - The Pump program key is `ConstraintMut` (2000), behind the quote mint
//!   check (6004) and ahead of every other stop.
//! - The event authority cannot receive SOL: the lamports are written before
//!   the event CPI, which fails with `UnbalancedInstruction`. On a token
//!   curve it receives through its token account like any wallet.

use crate::sweep_fees::{sweep, Bucket, QuoteMint, Recipient, Stop, Sweep, Swept, CURVE_RENT_MINIMUM,
                       MINT_DOES_NOT_MATCH_BONDING_CURVE};

pub const CONSTRAINT_MUT: u32 = 2000;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Role {
    Ordinary,
    Payer,
    Curve,
    EventAuthority,
    Program,
    Zero,
}

pub struct Case {
    pub role: Role,
    pub native: bool,
    pub mayhem: bool,
    pub wrong_quote: bool,
    pub real_quote: u64,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    pub curve_lamports: u64,
    pub recipient_lamports: u64,
    pub curve_quote_ata: u64,
    pub recipient_quote_ata_exists: bool,
}

#[derive(Debug, PartialEq, Eq)]
pub enum AliasStop {
    Base(Stop),
    Code(u32),
    UnbalancedInstruction,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Moved {
    pub swept: Swept,
    /// Lamports the payer spends, its recipient income not counted.
    pub payer_spends: u64,
    pub payer_gets: u64,
    pub curve_after: u64,
    pub recipient_after: u64,
    /// Tokens the curve's account loses.
    pub tokens: u64,
}

/// A curve already below its rent minimum may stay there as long as it ends
/// with no more lamports than it started with.
fn held_below_rent(c: &Case) -> bool {
    let reserved = c.real_quote + c.creator_fee + c.protocol_fees;
    let top_up = CURVE_RENT_MINIMUM.saturating_sub(c.curve_lamports.saturating_sub(reserved));
    c.curve_lamports < CURVE_RENT_MINIMUM && c.curve_lamports + top_up - c.protocol_fees <= c.curve_lamports
}

pub fn sweep_alias(c: &Case) -> Result<Moved, AliasStop> {
    if c.role == Role::Program {
        let code = if c.wrong_quote { MINT_DOES_NOT_MATCH_BONDING_CURVE } else { CONSTRAINT_MUT };
        return Err(AliasStop::Code(code));
    }
    let self_pay = c.role == Role::Curve;
    let quote_mint = match (c.wrong_quote, c.native) {
        (true, _) => QuoteMint::Other,
        (false, true) => QuoteMint::Native,
        (false, false) => QuoteMint::CurveQuote,
    };
    let recipient = match (c.role, c.mayhem) {
        (Role::Zero, _) => Recipient::Zero,
        (_, true) => Recipient::ReservedFeeRecipient,
        (_, false) => Recipient::FeeRecipient,
    };
    let base = Sweep {
        bucket: Bucket::Protocol,
        native: c.native,
        mayhem: c.mayhem,
        quote_mint,
        real_quote_reserves: c.real_quote,
        creator_fee: c.creator_fee,
        protocol_fees: c.protocol_fees,
        curve_lamports: c.curve_lamports,
        recipient,
        recipient_lamports: c.recipient_lamports,
        curve_quote_ata: Some(c.curve_quote_ata),
        recipient_quote_ata_exists: c.recipient_quote_ata_exists || self_pay,
    };
    let swept = match sweep(&base) {
        // The event CPI fails inside the call, ahead of the end-of-call rent check.
        Err(Stop::CurveBelowRent) if c.role == Role::EventAuthority => return Err(AliasStop::UnbalancedInstruction),
        Err(Stop::CurveBelowRent) if self_pay || held_below_rent(c) => {
            let reserved = c.real_quote + c.creator_fee + c.protocol_fees;
            Swept {
                amount: c.protocol_fees,
                curve_rent_top_up: CURVE_RENT_MINIMUM.saturating_sub(c.curve_lamports.saturating_sub(reserved)),
                buckets: (c.creator_fee, 0),
                ..Swept::default()
            }
        }
        other => other.map_err(AliasStop::Base)?,
    };
    if c.native && c.role == Role::EventAuthority && swept.amount > 0 {
        return Err(AliasStop::UnbalancedInstruction);
    }
    let lamports = if c.native { swept.amount } else { 0 };
    let tokens = if self_pay || c.native { 0 } else { swept.amount };
    Ok(Moved {
        payer_spends: swept.curve_rent_top_up + swept.recipient_ata_rent,
        payer_gets: if c.role == Role::Payer { lamports } else { 0 },
        curve_after: c.curve_lamports + swept.curve_rent_top_up - if self_pay { 0 } else { lamports },
        recipient_after: c.recipient_lamports + lamports,
        tokens,
        swept,
    })
}
