//! Recovered model of three Pump account-lifecycle instructions:
//! `init_user_volume_accumulator`, `close_user_volume_accumulator`, and
//! `extend_account`. It decides who pays or receives lamports, how large the
//! account ends up, and which check fails first. It is checked against the
//! captured program by `tests/test_account_lifecycle_captured.py`; matching
//! there is behavioural on the tested inputs only, not a byte-identity claim.

/// Default-rent cost of one data byte (`Rent::minimum_balance` is
/// `(128 + len) * 6960`).
pub const LAMPORTS_PER_BYTE: u64 = 6_960;
/// Allocated size of a UserVolumeAccumulator.
pub const UVA_LEN: u64 = 137;
/// Bytes Anchor needs to deserialize one (discriminator + 98 bytes of fields);
/// the remaining 31 are unused tail.
pub const UVA_FIELDS_END: u64 = 106;

pub const SYSTEM_ACCOUNT_IN_USE: u32 = 0;
pub const SYSTEM_INSUFFICIENT_FUNDS: u32 = 1;
pub const CONSTRAINT_OWNER: u32 = 2004;
pub const CONSTRAINT_RENT_EXEMPT: u32 = 2005;
pub const CONSTRAINT_SPACE: u32 = 2019;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const ACCOUNT_NOT_SIGNER: u32 = 3010;
pub const ACCOUNT_NOT_INITIALIZED: u32 = 3012;
pub const UNKNOWN_ACCOUNT_TYPE: u32 = 6010;

pub fn rent(len: u64) -> u64 {
    (128 + len) * LAMPORTS_PER_BYTE
}

/// The state of the account an instruction is pointed at.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Holder {
    /// No account (zero lamports).
    Missing,
    /// System-owned, no data, some lamports.
    SystemEmpty,
    /// System-owned with data.
    SystemWithData,
    /// Owned by some other program.
    OtherOwner,
    /// Owned by Pump: data length and whether the first 8 bytes are the
    /// discriminator the instruction expects.
    Pump { len: u64, disc_ok: bool },
}

/// Pump account types `extend_account` knows how to grow.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    BondingCurve,
    UserVolumeAccumulator,
    GlobalVolumeAccumulator,
    Global,
    /// Any other discriminator (including FeeConfig, SharingConfig, QuoteControl).
    Other,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    /// Runtime rejection: the account would end below its rent minimum.
    BelowRent,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Init {
    /// Lamports the payer moves into the accumulator.
    pub payer_paid: u64,
    /// A new account was created; otherwise only the `user` field is rewritten.
    pub created: bool,
}

/// `init_user_volume_accumulator` (Anchor `init_if_needed`, payer = `payer`).
/// `payer_available` is the payer's balance after the transaction fee.
pub fn init(uva: Holder, lamports: u64, payer_available: u64) -> Result<Init, Stop> {
    match uva {
        Holder::Missing | Holder::SystemEmpty => {
            // Only the shortfall is transferred, then allocate + assign.
            let paid = rent(UVA_LEN).saturating_sub(if uva == Holder::Missing { 0 } else { lamports });
            if paid > payer_available {
                return Err(Stop::Code(SYSTEM_INSUFFICIENT_FUNDS));
            }
            Ok(Init { payer_paid: paid, created: true })
        }
        Holder::SystemWithData => Err(Stop::Code(SYSTEM_ACCOUNT_IN_USE)),
        Holder::OtherOwner => Err(Stop::Code(ACCOUNT_OWNED_BY_WRONG_PROGRAM)),
        Holder::Pump { len, disc_ok } => {
            if len < 8 {
                return Err(Stop::Code(DISCRIMINATOR_NOT_FOUND));
            }
            if !disc_ok {
                return Err(Stop::Code(DISCRIMINATOR_MISMATCH));
            }
            if len < UVA_FIELDS_END {
                return Err(Stop::Code(DID_NOT_DESERIALIZE));
            }
            if len != UVA_LEN {
                return Err(Stop::Code(CONSTRAINT_SPACE));
            }
            if lamports < rent(UVA_LEN) {
                return Err(Stop::Code(CONSTRAINT_RENT_EXEMPT));
            }
            Ok(Init { payer_paid: 0, created: false })
        }
    }
}

/// `close_user_volume_accumulator`: every lamport goes to the user. Nothing
/// about unclaimed tokens, `needs_claim`, cashback, or the stored `user`
/// field is checked. Returns the refund.
pub fn close(uva: Holder, lamports: u64, user_signed: bool) -> Result<u64, Stop> {
    if !user_signed {
        return Err(Stop::Code(ACCOUNT_NOT_SIGNER));
    }
    match uva {
        Holder::Missing => Err(Stop::Code(ACCOUNT_NOT_INITIALIZED)),
        Holder::SystemEmpty | Holder::SystemWithData | Holder::OtherOwner => {
            Err(Stop::Code(ACCOUNT_OWNED_BY_WRONG_PROGRAM))
        }
        Holder::Pump { len, disc_ok } => {
            if len < 8 {
                return Err(Stop::Code(DISCRIMINATOR_NOT_FOUND));
            }
            if !disc_ok {
                return Err(Stop::Code(DISCRIMINATOR_MISMATCH));
            }
            if len < UVA_FIELDS_END {
                return Err(Stop::Code(DID_NOT_DESERIALIZE));
            }
            Ok(lamports)
        }
    }
}

pub fn target_len(kind: Kind) -> Option<u64> {
    match kind {
        Kind::BondingCurve => Some(166),
        Kind::UserVolumeAccumulator => Some(UVA_LEN),
        Kind::GlobalVolumeAccumulator => Some(600),
        Kind::Global => Some(1088),
        Kind::Other => None,
    }
}

#[derive(Debug, PartialEq, Eq)]
pub struct Extend {
    pub new_len: u64,
    /// Lamports the user pays; 0 means a no-op with no event.
    pub user_paid: u64,
}

/// `extend_account`. `owned_by_pump` is false for missing, system-owned, and
/// foreign accounts. `kind` is read from the first 8 bytes (ignored below 8).
pub fn extend(
    user_signed: bool,
    owned_by_pump: bool,
    kind: Kind,
    len: u64,
    lamports: u64,
    user_lamports: u64,
) -> Result<Extend, Stop> {
    if !user_signed {
        return Err(Stop::Code(ACCOUNT_NOT_SIGNER));
    }
    if !owned_by_pump {
        return Err(Stop::Code(CONSTRAINT_OWNER));
    }
    let target = if len < 8 { None } else { target_len(kind) };
    let Some(target) = target else { return Err(Stop::Code(UNKNOWN_ACCOUNT_TYPE)) };
    if len >= target {
        return Ok(Extend { new_len: len, user_paid: 0 });
    }
    // The size difference at the per-byte rate, whatever the account holds.
    let paid = (target - len) * LAMPORTS_PER_BYTE;
    if paid > user_lamports {
        return Err(Stop::Code(SYSTEM_INSUFFICIENT_FUNDS));
    }
    if lamports + paid < rent(target) {
        return Err(Stop::BelowRent);
    }
    Ok(Extend { new_len: target, user_paid: paid })
}
