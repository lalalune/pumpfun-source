//! Pure model of how `create_v2` turns the requested `creator_fee_bps` into
//! the value stored on the new bonding curve (`programs/pump/src/create_v2.rs`,
//! `execute`). Checked against the captured program by
//! `tests/test_create_fee_bounds_captured.py`.
//!
//! The request only counts for quote mints admitted through a QuoteControl
//! entry (`Controlled`) or a Pump-curve quote chain (`Nested`). For SOL
//! (no quote accounts, or the native/default mint) and for the Global
//! whitelisted quote mint the request is dropped and 0 is stored, whatever
//! its size and whatever the Global flags say. For the two counted sources a
//! nonzero request needs `Global.creator_fee_configurable` (else 6077) and
//! must not exceed `Global.max_configurable_creator_fee_bps` (else 6078);
//! the flag is checked first. A zero request stores 0 without reading either
//! field.

/// How `create_v2` admitted the quote mint.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum QuoteSource {
    Sol,
    Whitelisted,
    Controlled,
    Nested,
}

/// The two Global fields the fee gate reads (offsets 1045 and 1046).
#[derive(Clone, Copy, Debug)]
pub struct FeeGate {
    pub configurable: bool,
    pub max_bps: u64,
}

pub const CREATOR_FEE_NOT_CONFIGURABLE: u32 = 6077;
pub const CREATOR_FEE_BPS_OUT_OF_RANGE: u32 = 6078;

/// The `creator_fee_bps` written to the bonding curve and the CreateEvent,
/// or the Pump error code that stops the create.
pub fn stored_creator_fee(source: QuoteSource, requested: u64, gate: FeeGate) -> Result<u64, u32> {
    let counted = matches!(source, QuoteSource::Controlled | QuoteSource::Nested);
    if requested == 0 || !counted {
        return Ok(0);
    }
    if !gate.configurable {
        return Err(CREATOR_FEE_NOT_CONFIGURABLE);
    }
    if requested > gate.max_bps {
        return Err(CREATOR_FEE_BPS_OUT_OF_RANGE);
    }
    Ok(requested)
}
