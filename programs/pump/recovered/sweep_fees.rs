//! Captured accounting of Pump `sweep_protocol_fee` / `sweep_creator_fee`:
//! moving a bonding curve's accrued protocol or creator fee bucket to its
//! recipient, for native (SOL) curves and SPL-token quote curves.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured SPL
//! Token and Associated Token programs by `tests/test_sweep_fees_captured.py`.
//! Not linked into the SBF crate. This is not a byte-identity claim.

pub const NOT_AUTHORIZED: u32 = 6000;
pub const MINT_DOES_NOT_MATCH_BONDING_CURVE: u32 = 6004;
pub const OVERFLOW: u32 = 6024;
/// Anchor `ConstraintSeeds`.
pub const CONSTRAINT_SEEDS: u32 = 2006;
/// Anchor `AccountNotInitialized`.
pub const ACCOUNT_NOT_INITIALIZED: u32 = 3012;
/// SPL Token `InsufficientFunds`.
pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;
/// `Rent::minimum_balance(166)`, the BondingCurve size.
pub const CURVE_RENT_MINIMUM: u64 = 2_046_240;
/// `Rent::minimum_balance(0)`.
pub const ZERO_RENT_MINIMUM: u64 = 890_880;
/// `Rent::minimum_balance(165)`, an SPL token account.
pub const TOKEN_ACCOUNT_RENT: u64 = 2_039_280;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Bucket {
    Protocol,
    Creator,
}

/// Which quote mint account the caller passes, relative to the curve.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum QuoteMint {
    Native,
    CurveQuote,
    Other,
}

/// Who the recipient is.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Recipient {
    FeeRecipient,
    /// One of `global.fee_recipients` (stored sorted).
    FeeList,
    ReservedFeeRecipient,
    /// One of `global.reserved_fee_recipients`.
    ReservedList,
    /// The creator-vault PDA of the curve's creator.
    CreatorVault,
    Other,
    Zero,
}

pub struct Sweep {
    pub bucket: Bucket,
    /// `bonding_curve.quote_mint == Pubkey::default()`.
    pub native: bool,
    pub mayhem: bool,
    pub quote_mint: QuoteMint,
    pub real_quote_reserves: u64,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    pub curve_lamports: u64,
    pub recipient: Recipient,
    pub recipient_lamports: u64,
    /// Quote balance of the curve's quote ATA (`None`: not created).
    pub curve_quote_ata: Option<u64>,
    pub recipient_quote_ata_exists: bool,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    /// `sub_lamports` on a curve holding less than the amount.
    ArithmeticOverflow,
    /// Runtime rejection: the curve would end above zero but below its rent
    /// minimum (only reachable when its lamports are already short of the SOL
    /// it owes). Ending at exactly zero is accepted and drops the account.
    CurveBelowRent,
}

#[derive(Debug, Default, PartialEq, Eq)]
pub struct Swept {
    /// Amount swept (0: nothing to sweep, no event).
    pub amount: u64,
    /// Rent the payer adds to the curve before sweeping.
    pub curve_rent_top_up: u64,
    /// Rent the payer adds to a creator vault under the zero-byte minimum.
    pub vault_top_up: u64,
    /// Rent the payer spends creating the recipient's quote ATA.
    pub recipient_ata_rent: u64,
    /// Buckets after the sweep: (creator_fee, protocol_fees).
    pub buckets: (u64, u64),
}

pub fn sweep(s: &Sweep) -> Result<Swept, Stop> {
    let mint_ok = match s.quote_mint {
        QuoteMint::Native => s.native,
        QuoteMint::CurveQuote => !s.native,
        QuoteMint::Other => false,
    };
    if !mint_ok {
        return Err(Stop::Code(MINT_DOES_NOT_MATCH_BONDING_CURVE));
    }
    let mut out = Swept { buckets: (s.creator_fee, s.protocol_fees), ..Swept::default() };
    // The payer keeps the curve rent-exempt above the SOL it owes (native) or
    // above nothing (quote curves hold their reserves in the quote ATA).
    let reserved = if s.native {
        s.real_quote_reserves
            .checked_add(s.creator_fee.checked_add(s.protocol_fees).ok_or(Stop::Code(OVERFLOW))?)
            .ok_or(Stop::Code(OVERFLOW))?
    } else {
        0
    };
    let available = s.curve_lamports.saturating_sub(reserved);
    if CURVE_RENT_MINIMUM > available {
        out.curve_rent_top_up = CURVE_RENT_MINIMUM - available;
    }
    if s.recipient == Recipient::Zero {
        return Err(Stop::Code(NOT_AUTHORIZED));
    }
    let authorized = match (s.bucket, s.mayhem) {
        (Bucket::Creator, _) => {
            if s.recipient != Recipient::CreatorVault {
                return Err(Stop::Code(CONSTRAINT_SEEDS));
            }
            true
        }
        (Bucket::Protocol, true) => matches!(s.recipient, Recipient::ReservedFeeRecipient | Recipient::ReservedList),
        (Bucket::Protocol, false) => matches!(s.recipient, Recipient::FeeRecipient | Recipient::FeeList),
    };
    if !authorized {
        return Err(Stop::Code(NOT_AUTHORIZED));
    }
    let amount = match s.bucket {
        Bucket::Creator => std::mem::take(&mut out.buckets.0),
        Bucket::Protocol => std::mem::take(&mut out.buckets.1),
    };
    if amount == 0 {
        return Ok(out);
    }
    out.amount = amount;
    if s.native {
        if s.bucket == Bucket::Creator && s.recipient_lamports < ZERO_RENT_MINIMUM {
            // The whole minimum, not the shortfall.
            out.vault_top_up = ZERO_RENT_MINIMUM;
        }
        let curve = s.curve_lamports + out.curve_rent_top_up;
        if curve < amount {
            return Err(Stop::ArithmeticOverflow);
        }
        // The runtime accepts a curve drained to exactly zero lamports (the
        // account is then dropped) but rejects anything between 0 and rent.
        let left = curve - amount;
        if left != 0 && left < CURVE_RENT_MINIMUM {
            return Err(Stop::CurveBelowRent);
        }
    } else {
        let Some(balance) = s.curve_quote_ata else { return Err(Stop::Code(ACCOUNT_NOT_INITIALIZED)) };
        if !s.recipient_quote_ata_exists {
            out.recipient_ata_rent = TOKEN_ACCOUNT_RENT;
        }
        if balance < amount {
            return Err(Stop::Code(TOKEN_INSUFFICIENT_FUNDS));
        }
    }
    Ok(out)
}
