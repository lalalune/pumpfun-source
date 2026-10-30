//! Captured routing of the creator fee on Pump legacy `buy` and `sell` when the
//! bonding curve is a cashback coin, next to the regular creator-vault route.
//!
//! The trade amounts themselves (SOL in or out, protocol and creator fee) are
//! inputs here; this module only models where the creator fee goes, how the
//! user volume accumulator (UVA) is created or validated, how cashback is
//! credited, and the remaining-account order each route expects.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured Pump
//! Fees program by `tests/test_legacy_cashback_captured.py`. Not linked into
//! the SBF crate. This is not a byte-identity claim.

pub const OVERFLOW: u32 = 6024;
pub const BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED: u32 = 6057;
pub const BUYBACK_FEE_RECIPIENT_MISSING: u32 = 6062;
pub const MISSING_CASHBACK_ACCOUNTS: u32 = 6072;
pub const INVALID_CASHBACK_ACCUMULATOR: u32 = 6073;
pub const INVALID_BONDING_CURVE_V2: u32 = 6074;
/// Anchor `AccountDiscriminatorMismatch`.
pub const ACCOUNT_DISCRIMINATOR_MISMATCH: u32 = 3002;
/// Anchor `AccountOwnedByWrongProgram`.
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
/// `Rent::minimum_balance(0)` under default rent.
pub const VAULT_RENT_MINIMUM: u64 = 890_880;
/// `Rent::minimum_balance(137)`, the UserVolumeAccumulator size.
pub const UVA_RENT_MINIMUM: u64 = 1_844_400;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Side {
    Buy,
    Sell,
}

/// State of the user's `user_volume_accumulator` PDA before the trade.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Uva {
    Missing,
    /// System-owned, no data, holding some lamports.
    Funded(u64),
    /// Pump-owned with the right discriminator (rent-exempt balance).
    Valid { lamports: u64, cashback_earned: u64 },
    ForeignOwner,
    BadDiscriminator,
}

/// What a remaining-account slot holds.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Slot {
    Absent,
    CurveV2,
    Uva,
    Buyback,
    Other,
}

pub struct Trade {
    pub side: Side,
    pub cashback_coin: bool,
    /// Creator fee and bps as priced for this trade (0 when the curve has no creator).
    pub creator_fee: u64,
    pub creator_bps: u64,
    pub uva: Uva,
    pub vault_lamports: u64,
    pub remaining: [Slot; 3],
}

#[derive(Debug, PartialEq, Eq)]
pub struct Route {
    /// Rent the user pays to create the UVA (part of `uva_credit`).
    pub uva_rent: u64,
    /// Total lamports the UVA gains.
    pub uva_credit: u64,
    /// Lamports the creator vault gains, including any rent top-up.
    pub vault_credit: u64,
    /// Rent top-up the user pays into the creator vault.
    pub vault_top_up: u64,
    /// `cashback_earned` after the trade, `None` when no UVA exists afterwards.
    pub cashback_earned: Option<u64>,
    pub event_creator_bps: u64,
    pub event_creator_fee: u64,
    pub event_cashback_bps: u64,
    pub event_cashback: u64,
}

fn rent_shortfall(uva: Uva) -> u64 {
    match uva {
        Uva::Missing => UVA_RENT_MINIMUM,
        Uva::Funded(lamports) => UVA_RENT_MINIMUM.saturating_sub(lamports),
        _ => 0,
    }
}

fn earned_before(uva: Uva) -> u64 {
    match uva {
        Uva::Valid { cashback_earned, .. } => cashback_earned,
        _ => 0,
    }
}

fn buyback_at(remaining: &[Slot; 3], index: usize) -> Result<(), u32> {
    match remaining[index] {
        Slot::Absent => Err(BUYBACK_FEE_RECIPIENT_MISSING),
        Slot::Buyback => Ok(()),
        _ => Err(BUYBACK_FEE_RECIPIENT_NOT_AUTHORIZED),
    }
}

pub fn route(t: &Trade) -> Result<Route, u32> {
    let mut r = Route {
        uva_rent: 0,
        uva_credit: 0,
        vault_credit: 0,
        vault_top_up: 0,
        cashback_earned: None,
        event_creator_bps: t.creator_bps,
        event_creator_fee: t.creator_fee,
        event_cashback_bps: 0,
        event_cashback: 0,
    };
    let fee = t.creator_fee;
    let cashback = fee != 0 && t.cashback_coin;
    match t.side {
        Side::Buy => {
            // The UVA is a named `init_if_needed` account: Anchor validates or
            // creates it before the handler, on every coin and every route.
            match t.uva {
                Uva::ForeignOwner => return Err(ACCOUNT_OWNED_BY_WRONG_PROGRAM),
                Uva::BadDiscriminator => return Err(ACCOUNT_DISCRIMINATOR_MISMATCH),
                _ => {}
            }
            r.uva_rent = rent_shortfall(t.uva);
            r.cashback_earned = Some(earned_before(t.uva));
            // The buyback recipient at index 1 is resolved before the creator fee.
            buyback_at(&t.remaining, 1)?;
            if fee != 0 && t.remaining[0] != Slot::CurveV2 {
                return Err(INVALID_BONDING_CURVE_V2);
            }
        }
        Side::Sell => {
            if cashback {
                match t.remaining[0] {
                    Slot::Absent => return Err(MISSING_CASHBACK_ACCOUNTS),
                    Slot::Uva => {}
                    _ => return Err(INVALID_CASHBACK_ACCUMULATOR),
                }
                match t.uva {
                    Uva::Missing | Uva::Funded(_) => r.uva_rent = rent_shortfall(t.uva),
                    Uva::Valid { .. } => {}
                    Uva::ForeignOwner | Uva::BadDiscriminator => return Err(INVALID_CASHBACK_ACCUMULATOR),
                }
                r.cashback_earned = Some(earned_before(t.uva));
            } else if fee != 0 && t.remaining[0] != Slot::CurveV2 {
                return Err(INVALID_BONDING_CURVE_V2);
            }
            if let Uva::Valid { cashback_earned, .. } = t.uva {
                r.cashback_earned.get_or_insert(cashback_earned);
            }
        }
    }
    if cashback {
        let earned = r.cashback_earned.unwrap_or(0).checked_add(fee).ok_or(OVERFLOW)?;
        r.cashback_earned = Some(earned);
        r.uva_credit = r.uva_rent + fee;
        r.event_creator_bps = 0;
        r.event_creator_fee = 0;
        r.event_cashback_bps = t.creator_bps;
        r.event_cashback = fee;
    } else {
        r.uva_credit = r.uva_rent;
        if fee != 0 {
            // A vault under the zero-byte minimum is topped up by the whole minimum.
            r.vault_top_up = if t.vault_lamports < VAULT_RENT_MINIMUM { VAULT_RENT_MINIMUM } else { 0 };
            r.vault_credit = r.vault_top_up + fee;
        }
    }
    if t.side == Side::Sell {
        if cashback && t.remaining[1] != Slot::CurveV2 {
            return Err(INVALID_BONDING_CURVE_V2);
        }
        // The cashback route consumes [uva, bonding_curve_v2], shifting the
        // buyback recipient from index 1 to index 2.
        buyback_at(&t.remaining, if cashback { 2 } else { 1 })?;
    }
    Ok(r)
}
